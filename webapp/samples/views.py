import logging
import shutil
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import pyminizip
from django.conf import Path, settings
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q, Window
from django.db.models.functions import RowNumber
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import loader

from .github import Github
from .models import DewolfError, GitHubIssue, Summary
from .utils import (get_file_last_modified_and_content, get_last_line, get_progress, is_hex,
                    sha256sum, unzip_flat)


@login_required
def index(request):
    """
    Index view, list smallest cases per case group
    """
    # query summary for current dewolf commit
    summary = Summary.objects.using("samples").order_by("-id").first()

    if summary is None:
        context = {
            "quickrun_errors": [],
            "longrun_errors": [],
            "summary": None,
            "issues": defaultdict(list),
            "message": "No summary data available.",
        }
        template = loader.get_template("index.html")
        return HttpResponse(template.render(context, request))

    def _smallest_sample_per_case_group_and_tag(commit: str, tag: Optional[str]):
        """
        Return query set containing the smallest representative of each case group,
        given commit and run-type.
        """
        # select the smallest representative from a case group
        errors_current_commit = DewolfError.objects.using("samples").filter(dewolf_current_commit=commit, tag=tag)
        # annotate each error wit row number, partition by 'case_group', and ordered by #basicblocks
        rows_minimized_per_group = errors_current_commit.annotate(
            row_number=Window(expression=RowNumber(), partition_by=[F("case_group")], order_by=F("function_basic_block_count").asc())
        )
        # select representative with least basic blocks, then order by error count descending
        return rows_minimized_per_group.filter(row_number=1).order_by("-errors_per_group_count_pre_filter")

    quickrun_errors = _smallest_sample_per_case_group_and_tag(summary.dewolf_current_commit, "quick")
    longrun_errors = _smallest_sample_per_case_group_and_tag(summary.dewolf_current_commit, "long")
    untagged_errors = _smallest_sample_per_case_group_and_tag(summary.dewolf_current_commit, None)

    # retrieve all GitHub issues, group them in a default dict by 'case_group'
    github_issues_by_case_group = defaultdict(list)
    for issue in GitHubIssue.objects.using("samples").all():
        github_issues_by_case_group[issue.case_group].append(issue)

    template = loader.get_template("index.html")
    context = {
        "quickrun_errors": quickrun_errors,
        "longrun_errors": longrun_errors,
        "untagged_errors": untagged_errors,
        "summary": summary,
        "issues": github_issues_by_case_group,
    }
    return HttpResponse(template.render(context, request))


def timestamp_to_elapsed_seconds(timestamp) -> int:
    delta_seconds = (datetime.now() - datetime.fromtimestamp(timestamp)).total_seconds()
    return int(delta_seconds)


@login_required
def dashboard(request):

    last_heartbeat, health_stats = get_file_last_modified_and_content(Path(settings.BASE_DIR) / "data/healthcheck.txt")
    last_idle, _ = get_file_last_modified_and_content(Path(settings.BASE_DIR) / "data/idle")
    progress_log = get_last_line(Path(settings.BASE_DIR) / "data/progress.log")
    template = loader.get_template("dashboard.html")
    context = {
        "health_stats": health_stats,
        "progress_log": progress_log,
        "heartbeat_delta": timedelta(seconds=timestamp_to_elapsed_seconds(last_heartbeat)),
        "idle_delta": timedelta(seconds=timestamp_to_elapsed_seconds(last_idle)),
    }
    context["quickrun_processed"], context["quickrun_total"] = get_progress(Path(settings.BASE_DIR) / "data/quick_run.progress")
    context["longrun_processed"], context["longrun_total"] = get_progress(Path(settings.BASE_DIR) / "data/long_run.progress")
    return HttpResponse(template.render(context, request))


@login_required
def search(request):
    query = request.GET.get("q")
    template = loader.get_template("search.html")
    if is_hex(query) and len(query) >= 4:
        results = DewolfError.objects.using("samples").filter(sample_hash__startswith=query)
    else:
        results = DewolfError.objects.using("samples").filter(Q(dewolf_exception__icontains=query) | Q(dewolf_traceback__icontains=query))

    context = {"results": results}
    return HttpResponse(template.render(context, request))


@login_required
def dewolf_error(request, row_id):
    dewolf_error = DewolfError.objects.using("samples").get(id=row_id)
    related_cases = (
        DewolfError.objects.using("samples")
        .filter(case_group=dewolf_error.case_group)
        .exclude(id=row_id)
        .order_by("function_basic_block_count")
    )[:10]
    try:
        issues = GitHubIssue.objects.using("samples").filter(case_group=dewolf_error.case_group).all()
    except GitHubIssue.DoesNotExist:
        issues = []

    context = {"failed_case": dewolf_error, "related_cases": related_cases, "issues": issues}
    template = loader.get_template("dewolf_error.html")
    return HttpResponse(template.render(context, request))


@login_required
def samples(request):
    summary = Summary.objects.using("samples").order_by("-id").all()
    context = {"summary": summary, "avg_duration": "not implemented"}
    template = loader.get_template("samples.html")
    return HttpResponse(template.render(context, request))


@login_required
def download_sample(request, sample_hash):
    """Given sample hash, download zipped (and password protected) sample"""

    if not is_hex(sample_hash):
        raise Http404()

    if not (sample_file := Path(settings.SAMPLE_DIR) / sample_hash).exists():
        sample_file = Path(settings.SAMPLE_COLD_STORAGE) / sample_hash

    with tempfile.TemporaryDirectory() as tdir:
        zip_path = Path(tdir) / f"{sample_hash}.zip"
        try:
            pyminizip.compress(sample_file.as_posix(), None, zip_path.as_posix(), settings.ZIP_PASSWORD, settings.ZIP_COMPRESSION_LEVEL)
        except OSError:
            raise Http404("sample does not exist")
        return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=f"{sample_hash}.zip")


def get_issue_status(issue) -> str:
    status = issue["state"]
    if status == "open" and issue["assignee"] is not None:
        return "in progress"
    return status


def _case_group_from_title(title: str) -> str:
    return title[1 : title.find("]")]


def _update_issues():
    """
    Iterate repo issues (tagged 'bugfinder'), match them to case group and write to issue db
    """
    issues = []
    repo = Github(settings.GITHUB_TOKEN, settings.GITHUB_REPO_OWNER, settings.GITHUB_REPO_NAME)
    for title, issue in repo.existing_issue_titles_to_issue_map.items():
        issues.append(f"#{issue['number']}: {get_issue_status(issue)}")
        try:
            db_issue = GitHubIssue.objects.using("samples").get(number=issue["number"])
            db_issue.status = get_issue_status(issue)
            db_issue.updated_at = datetime.now()
            db_issue.save()
        except GitHubIssue.DoesNotExist:
            github_issue = GitHubIssue.objects.using("samples").create(
                case_group=_case_group_from_title(title),
                title=title,
                description="",
                status=get_issue_status(issue),
                number=issue["number"],
                html_url=issue["html_url"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            github_issue.save()
    return issues


@login_required
def update_issues(request):
    try:
        issues = _update_issues()
        response = {"message": f'Success! {" ".join(issues)}', "status": 200}
    except Exception as ex:
        response = {"message": f"ERROR: {ex}", "status": 500}
    context = {"response": response}
    template = loader.get_template("update.html")
    return HttpResponse(template.render(context, request))


@login_required
def create_github_issue(request, case_id):
    dewolf_error = DewolfError.objects.using("samples").get(id=case_id)

    if request.method == "GET":
        # display issue
        try:
            db_issue = GitHubIssue.objects.using("samples").get(case_group=dewolf_error.case_group)
            # TODO display issue information
            return HttpResponse(str(db_issue))
        except GitHubIssue.DoesNotExist:
            raise Http404()
    elif request.method == "POST":
        # create issue
        context = {"issue": dewolf_error}
        issue_title = f"[{dewolf_error.case_group}] {dewolf_error.dewolf_exception}"
        issue_text = loader.render_to_string("issue.md", context)
        repo = Github(settings.GITHUB_TOKEN, settings.GITHUB_REPO_OWNER, settings.GITHUB_REPO_NAME)
        if (issue := repo.create_issue(title=issue_title, body=issue_text)) is not None:
            # Create a new instance of the GitHubIssue model
            github_issue = GitHubIssue.objects.using("samples").create(
                case_group=dewolf_error.case_group,
                title=issue_title,
                description="",
                status=get_issue_status(issue),
                number=issue["number"],
                html_url=issue["html_url"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            github_issue.save()
        else:
            logging.warning("no issue was created")
        return redirect(request.META["HTTP_REFERER"])


def move_to_coldstorage(file_path: Path):
    sample_hash = sha256sum(file_path)
    shutil.move(file_path, Path(settings.SAMPLE_COLD_STORAGE) / sample_hash)
    return sample_hash


def handle_zip_file(zipfile_path):
    with tempfile.TemporaryDirectory() as tdir:
        response_data = {"message": "extracted from zip file:", "sample_hashes": []}
        try:
            unzip_flat(zipfile_path, tdir, pwd=settings.ZIP_PASSWORD)
        except Exception as ex:
            response_data["message"] = str(ex)
            logging.error(f"unzip: {ex}")
            return 500, response_data
        for sample in Path(tdir).iterdir():
            if not sample.is_file():
                continue
            sample_hash = move_to_coldstorage(sample)
            response_data["sample_hashes"].append(sample_hash)
        return 200, response_data


def handle_file(file_path):
    sample_hash = move_to_coldstorage(file_path)
    response_data = {"message": "uploaded sample hash:", "sample_hashes": [sample_hash]}
    return 200, response_data


@login_required
def upload(request):
    if request.method == "POST" and request.FILES:
        file = request.FILES.get("file")

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file.read())
            temp_file.flush()

            if file.content_type == "application/zip":
                status, response_data = handle_zip_file(temp_file.name)
            else:
                status, response_data = handle_file(temp_file.name)
            return JsonResponse(response_data, status=status)
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def upload_view(request):
    context = {}
    template = loader.get_template("upload.html")
    return HttpResponse(template.render(context, request))
