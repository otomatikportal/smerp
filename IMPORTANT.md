# Validation and Serialization in Django REST Framework

## Ordered Validation in Serializers

When you define a serializer with custom field-level and object-level validation, the order of validation is as follows:

### Example Serializer
```python
class OrderedValidationSerializer(serializers.Serializer):
    field1 = serializers.CharField()
    field2 = serializers.CharField()
    
    def validate_field1(self, value):
        print("1. Field-level validation for field1")
        return value
    
    def validate_field2(self, value):
        print("2. Field-level validation for field2")
        return value
    
    def validate(self, data):
        print("3. Object-level validation (after all fields)")
        return data
```

### Validation Workflow
1. **Built-in Field Validations**  
   The built-in validations for fields (e.g., `CharField`, `EmailField`) are executed first.

2. **Custom Field Validations**  
   Custom validation methods, such as `validate_field1` and `validate_field2`, are called for each field.

3. **Object-level Validation**  
   The `validate` method is executed after all field-level validations are complete.

When you call `serializer.is_valid()`, the above validations run in the described order.

---

## Update Methods in ViewSets vs. Serializers

### ModelViewSet Update Methods
- **`update` Method**: Corresponds to the HTTP `PUT` method.
- **`partial_update` Method**: Corresponds to the HTTP `PATCH` method.

### Serializer Update Methods
- Serializers only have an `update` method and do not include a `partial_update` method.

### Behavior with `partial_update`
When the `partial_update` method is called on a `ModelViewSet`:
- A `partial=True` flag is passed to the serializer.
- This flag ensures that:
  - **Field-level validation (`validate_<fieldname>`)** is not executed for fields that are not provided in the request data.
  - **Object-level validation (`validate` method)** uses the value from the instance for missing fields during the validation process.

This distinction is crucial as it allows partial updates to work correctly without requiring all fields to be present or validated.

---

## Key Takeaways
- The order of validation in serializers ensures that field-level validations are executed before object-level validations. 
- `partial=True` in `partial_update` facilitates partial updates by bypassing field-level validation for missing fields and utilizing instance values for object-level validation.