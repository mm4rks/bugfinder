from django.http import Http404, HttpResponse
from django.template import loader
from .models import Sample


def index(request):
    # total_cases = Sample.objects.using("samples").count()
    failed_cases = Sample.objects.using("samples").filter(is_successful__startswith="0")
    # output = f"{total_cases}:{total_fails}"
    template = loader.get_template("index.html")
    context = {
            "failed_cases": failed_cases
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
    context = {
            "failed_case": Sample.objects.using("samples").get(id=case_id)
            }
    template = loader.get_template("case.html")
    return HttpResponse(template.render(context, request))
