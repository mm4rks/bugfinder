from django.db import models

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

class Summary(models.Model):
    dewolf_current_commit = models.TextField(blank=True, null=True)  # This field type is a guess.
    avg_dewolf_decompilation_time = models.FloatField(blank=True, null=True)  # This field type is a guess.
    total_functions = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    total_errors = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    unique_exceptions = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    unique_tracebacks = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    processed_samples = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    tag = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'summary'


class DewolfError(models.Model):
    function_name = models.TextField(blank=True, null=True)  # This field type is a guess.
    function_basic_block_count = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    function_size = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    function_arch = models.TextField(blank=True, null=True)  # This field type is a guess.
    function_platform = models.TextField(blank=True, null=True)  # This field type is a guess.
    sample_hash = models.TextField(blank=True, null=True)  # This field type is a guess.
    sample_name = models.TextField(blank=True, null=True)  # This field type is a guess.
    sample_total_function_count = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    sample_decompilable_function_count = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    dewolf_current_commit = models.TextField(blank=True, null=True)  # This field type is a guess.
    binaryninja_version = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_max_basic_blocks = models.IntegerField(blank=False, null=True)
    dewolf_exception = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_traceback = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_decompilation_time = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    dewolf_undecorated_code = models.TextField(blank=True, null=True)  # This field type is a guess.
    is_successful = models.BooleanField(blank=True, null=True)  # This field type is a guess.
    timestamp = models.TextField(blank=True, null=True)  # This field type is a guess.
    error_file_path = models.TextField(blank=True, null=True)  # This field type is a guess.
    error_line = models.TextField(blank=True, null=True)  # This field type is a guess.
    case_group = models.TextField(blank=True, null=True)  # This field type is a guess.
    errors_per_group_count_pre_filter = models.IntegerField(blank=True, null=True)  # This field type is a guess.
    tag = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dewolf_errors'

class GitHubIssue(models.Model):
    case_group = models.TextField()
    title = models.TextField()
    description = models.TextField()
    status = models.CharField(max_length=100)
    number = models.IntegerField()
    html_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
