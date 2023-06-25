# What happened?

```python
{% autoescape off %}
{{ issue.dewolf_traceback }}
{% endautoescape %}
```

Error class `{{ issue.case_group }}` contains **{{ issue.errors_per_group_count_pre_filter }}** cases.


# How to reproduce?

```bash
python decompile.py {{ issue.sample_hash }} {{ issue.function_name }} --debug
```

sample: [{{ issue.sample_hash }}](https://bugfinder.seclab-bonn.de/download/{{ issue.sample_hash }})
case: https://bugfinder.seclab-bonn.de/case/{{ issue.id }}/
dewolf commit: {{ issue.dewolf_current_commit }}
Binaryninja version: `{{ issue.binaryninja_version }}`
