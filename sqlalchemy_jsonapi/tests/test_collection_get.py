import pytest


def test_no_query():
    raise NotImplementedError


def describe_include():
    def single():
        raise NotImplementedError

    def single_skipping_connecting_model():
        raise NotImplementedError

    def multiple_models():
        raise NotImplementedError

    def not_a_relationship():
        raise NotImplementedError


def describe_fields():
    def single():
        raise NotImplementedError

    def multiple_fields():
        raise NotImplementedError

    def across_relationships():
        raise NotImplementedError

    def not_a_field():
        raise NotImplementedError

    def bad_seperator():
        raise NotImplementedError


def describe_sort():
    def single():
        raise NotImplementedError

    def multiple():
        raise NotImplementedError

    def not_a_field():
        raise NotImplementedError

    def bad_separator():
        raise NotImplementedError

    def bad_operator():
        raise NotImplementedError


def describe_page():
    def pagination():
        raise NotImplementedError

    def limit_offset():
        raise NotImplementedError

    def out_of_range():
        raise NotImplementedError


def describe_filter():
    def simple_single():
        raise NotImplementedError

    def not_a_field():
        raise NotImplementedError

    def returns_empty_collection():
        raise NotImplementedError
