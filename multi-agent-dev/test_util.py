# Test the string formatting
class DateTime:
    def __init__(self, year=2024, month=5, day=11):
        self.year = year
        self.month = month
        self.day = day

def test_dart_string_template():
    date = DateTime()
    
    # Test the fixed line
    result = r"${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}"
    print(f"Test result: {result}")
    
    # This should now return a raw string with the Dart template syntax intact
    # instead of trying to interpolate Python variables
    
if __name__ == "__main__":
    test_dart_string_template()