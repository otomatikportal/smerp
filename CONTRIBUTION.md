```
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

# When you call serializer.is_valid(), it runs:
# 1. Built-in field validations (CharField, EmailField, etc.)
# 2. Custom field validations (validate_field1, validate_field2)
# 3. Object-level validation (validate method)