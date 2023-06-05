import tempfile
import pyminizip

from django.db.models import Avg, Count, OuterRef, Subquery
from django.http import FileResponse, Http404, HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.conf import Path, settings

from .models import Sample, Summary, DewolfError


@login_required
def index(request):
    failed_cases = DewolfError.objects.using("samples").filter(is_successful=False)
    # select the smallest representative from a case group
    subquery_min_ids = (
        failed_cases.filter(case_group=OuterRef("case_group")).order_by("function_basic_block_count").values("id")
    )
    min_dewolf_exceptions = (
        failed_cases.filter(id=Subquery(subquery_min_ids[:1]))
        .order_by("-errors_per_group_count_pre_filter")
    )
    template = loader.get_template("index.html")
    context = {"dewolf_errors": min_dewolf_exceptions}
    return HttpResponse(template.render(context, request))

@login_required
def dewolf_error(request, row_id):
    dewolf_error = DewolfError.objects.using("samples").get(id=row_id)
    related_cases = (
            DewolfError.objects.using("samples").filter(case_group=dewolf_error.case_group).exclude(id=row_id)
            .order_by("function_basic_block_count")
            )
    context = {"failed_case": dewolf_error, "related_cases": related_cases}
    template = loader.get_template("dewolf_error.html")
    return HttpResponse(template.render(context, request))

@login_required
def sample(request, sample_hash):
    output = f"Sample: {sample_hash}"
    try:
        sample_entries = Sample.objects.using("samples").filter(sample_hash__exact=sample_hash)
    except Sample.DoesNotExist:
        raise Http404("Sample does not exist")
    return HttpResponse(output)

@login_required
def samples(request):
    summary = Summary.objects.using("samples").all().first()
    context = {"summary": summary}
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


