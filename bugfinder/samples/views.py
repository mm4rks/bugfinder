from django.db.models import OuterRef, Subquery
from django.http import Http404, HttpResponse
from django.template import loader

from .models import Sample


def index(request):
    failed_cases = Sample.objects.using("samples").filter(is_successful__startswith="0")
    min_ids = failed_cases.filter(dewolf_exception=OuterRef("dewolf_exception"))\
            .order_by("function_basic_block_count").values("id")
    min_dewolf_exceptions = failed_cases.filter(id=Subquery(min_ids[:1]))
    template = loader.get_template("index.html")
    context = {
            "failed_cases": min_dewolf_exceptions
            }
    return HttpResponse(template.render(context, request))

def sample(request, sample_hash):
    output = f"Sample: {sample_hash}"
    try:
        sample_entries = Sample.objects.using("samples").filter(sample_hash__exact=sample_hash)
    except Sample.DoesNotExist:
        raise Http404("Sample does not exist")
    return HttpResponse(output)

# def failed_cases(request, case_id):
#     pass

def case(request, case_id):
    dewolf_exception = Sample.objects.using("samples").get(id=case_id)
    related_cases = Sample.objects.using("samples")\
            .filter( dewolf_exception=dewolf_exception.dewolf_exception).exclude(id=case_id)
    context = {
            "failed_case": Sample.objects.using("samples").get(id=case_id),
            "related_cases": related_cases
            }
    template = loader.get_template("case.html")
    return HttpResponse(template.render(context, request))
