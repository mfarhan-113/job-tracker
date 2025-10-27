"""
Core serializers for the apptrack project.
"""
from rest_framework import serializers


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """
    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            # Drop any fields that are specified in the `exclude` argument.
            excluded = set(exclude)
            for field_name in excluded:
                self.fields.pop(field_name, None)


class EmptySerializer(serializers.Serializer):
    """
    Empty serializer for endpoints that don't require any input.
    """
    pass
