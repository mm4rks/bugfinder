from django.db import models

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


class Sample(models.Model):
    function_name = models.TextField(blank=True, null=True)  # This field type is a guess.
    function_basic_block_count = models.TextField(blank=True, null=True)  # This field type is a guess.
    function_size = models.TextField(blank=True, null=True)  # This field type is a guess.
    function_arch = models.TextField(blank=True, null=True)  # This field type is a guess.
    function_platform = models.TextField(blank=True, null=True)  # This field type is a guess.
    sample_hash = models.TextField(blank=True, null=True)  # This field type is a guess.
    sample_name = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_options = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_current_commit = models.TextField(blank=True, null=True)  # This field type is a guess.
    binaryninja_version = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_exception = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_traceback = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_decompilation_time = models.TextField(blank=True, null=True)  # This field type is a guess.
    dewolf_undecorated_code = models.TextField(blank=True, null=True)  # This field type is a guess.
    is_successful = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'dewolf'
