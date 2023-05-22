import tempfile
import pyminizip

from django.db.models import Avg, Count, OuterRef, Subquery
from django.http import FileResponse, Http404, HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.conf import Path, settings

from .models import Sample


@login_required
def index(request):
    failed_cases = Sample.objects.using("samples").filter(is_successful=False)
    stats = {"version": "TODO", 
             "functions": Sample.objects.using("samples").count(), 
             "samples": Sample.objects.using("samples").values("sample_hash").distinct().count(), 
             "errors": failed_cases.count(),
             # "size_avg": round(Sample.objects.using("samples").aggregate(avg=Avg("function_basic_block_count"))["avg"], 4),
             # "time_avg": round(Sample.objects.using("samples").aggregate(avg=Avg("dewolf_decompilation_time"))["avg"], 4)
             "size_avg": -1,
             "time_avg": -1,
             }

    subquery_exception_count = (
        failed_cases.filter(dewolf_exception=OuterRef("dewolf_exception"))
        .values("dewolf_exception")
        .annotate(exception_count=Count("dewolf_exception"))
        .values("exception_count")
    )
    subquery_min_ids = (
        failed_cases.filter(dewolf_exception=OuterRef("dewolf_exception")).order_by("function_basic_block_count").values("id")
    )
    min_dewolf_exceptions = (
        failed_cases.filter(id=Subquery(subquery_min_ids[:1]))
        .annotate(exception_count=Subquery(subquery_exception_count))
        .order_by("-exception_count")
    )
    template = loader.get_template("index.html")
    context = {"dewolf_errors": min_dewolf_exceptions, "stats": stats}
    return HttpResponse(template.render(context, request))


@login_required
def sample(request, sample_hash):
    output = f"Sample: {sample_hash}"
    try:
        sample_entries = Sample.objects.using("samples").filter(sample_hash__exact=sample_hash)
    except Sample.DoesNotExist:
        raise Http404("Sample does not exist")
    return HttpResponse(output)

def debug(request):
    template = loader.get_template("base.html")
    context = {}
    return HttpResponse(template.render(context, request))

@login_required
def download_sample(request, sample_hash):

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


@login_required
def dewolf_error(request, row_id):
    dewolf_exception = Sample.objects.using("samples").get(id=row_id)
    related_cases = Sample.objects.using("samples").filter(dewolf_exception=dewolf_exception.dewolf_exception).exclude(id=row_id)
    context = {"failed_case": Sample.objects.using("samples").get(id=row_id), "related_cases": related_cases}
    template = loader.get_template("dewolf_error.html")
    return HttpResponse(template.render(context, request))
