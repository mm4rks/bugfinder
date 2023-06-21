import logging
import tempfile
from datetime import datetime

import pyminizip
from django.conf import Path, settings
from django.contrib.auth.decorators import login_required
from django.db import connections
from django.db.models import (Avg, CharField, Count, IntegerField, OuterRef, TextField,
                              Subquery, Value)
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect
from django.template import loader

from .github import Github
from .models import DewolfError, GitHubIssue, Sample, Summary


@login_required
def index(request):
    """
    Index view, list smallest cases per case group
    """
    # select the smallest representative from a case group
    failed_cases = DewolfError.objects.using("samples").filter(is_successful=False)
    subquery_min_ids = failed_cases.filter(case_group=OuterRef("case_group")).order_by("function_basic_block_count").values("id")
    min_dewolf_exceptions = failed_cases.filter(id=Subquery(subquery_min_ids[:1])).order_by("-errors_per_group_count_pre_filter")

    # Annotate min_dewolf_exceptions with the number and status of GitHubIssue
    github_issue_subquery = GitHubIssue.objects.using("samples").filter(case_group=OuterRef("case_group")).values("number", "status")
    min_dewolf_exceptions = min_dewolf_exceptions.annotate(
        issue_number=Coalesce(Subquery(github_issue_subquery.values("number")[:1]), Value(None, output_field=IntegerField())),
        issue_status=Coalesce(Subquery(github_issue_subquery.values("status")[:1]), Value("", output_field=CharField())),
        issue_html_url=Coalesce(Subquery(github_issue_subquery.values("html_url")[:1]), Value("", output_field=TextField())),
    )
    template = loader.get_template("index.html")
    context = {"dewolf_errors": min_dewolf_exceptions}
    return HttpResponse(template.render(context, request))


@login_required
def dewolf_error(request, row_id):
    dewolf_error = DewolfError.objects.using("samples").get(id=row_id)
    related_cases = (
        DewolfError.objects.using("samples")
        .filter(case_group=dewolf_error.case_group)
        .exclude(id=row_id)
        .order_by("function_basic_block_count")
    )
    # get issue
    try:
        issue = GitHubIssue.objects.using("samples").get(case_group=dewolf_error.case_group)
    except GitHubIssue.DoesNotExist:
        issue = None

    context = {"failed_case": dewolf_error, "related_cases": related_cases, "issue": issue}
    template = loader.get_template("dewolf_error.html")
    return HttpResponse(template.render(context, request))


@login_required
def sample(request, sample_hash):
    try:
        sample_entries = Sample.objects.using("samples").filter(sample_hash__exact=sample_hash)
    except Sample.DoesNotExist:
        raise Http404("Sample does not exist")
    context = {"samples": sample_entries}
    template = loader.get_template("sample.html")
    return HttpResponse(template.render(context, request))


@login_required
def samples(request):
    summary = Summary.objects.using("samples").all().first()
    average_duration = Sample.objects.using("samples").aggregate(avg_duration=Avg('duration_seconds'))
    context = {"summary": summary, "avg_duration": average_duration['avg_duration']}
    template = loader.get_template("samples.html")
    return HttpResponse(template.render(context, request))


@login_required
def download_sample(request, sample_hash):
    """Given sample hash, download zipped (and password protected) sample"""

    def is_hex(value):
        """Fast check if hex for small strings (<100)"""
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    if not is_hex(sample_hash):
        raise Http404()

    with tempfile.TemporaryDirectory() as tdir:
        sample_file = Path(settings.SAMPLE_DIR) / sample_hash
        zip_path = Path(tdir) / f"{sample_hash}.zip"
        try:
            pyminizip.compress(sample_file.as_posix(), None, zip_path.as_posix(), settings.ZIP_PASSWORD, settings.ZIP_COMPRESSION_LEVEL)
        except OSError:
            raise Http404("sample does not exist (OSError)")
        return FileResponse(open(zip_path, "rb"), as_attachment=True, filename=f"{sample_hash}.zip")


def get_issue_status(issue) -> str:
    status = issue["state"]
    if status == "open" and issue["assignee"] is not None:
        return "in progress"
    return status


def _case_group_from_title(title: str) -> str:
    return title[1: title.find("]")]


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
    issues = _update_issues()
    return HttpResponse("\n".join(issues))


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
