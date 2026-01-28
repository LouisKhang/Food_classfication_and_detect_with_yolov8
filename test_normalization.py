"""
Test script để kiểm tra cách chuẩn hóa tên class
"""
import json

# Load food data
with open('food_36.json', 'r', encoding='utf-8') as f:
    food_data = json.load(f)

print("Keys trong food_36.json:")
for key in sorted(food_data.keys())[:10]:
    print(f"  {key}")

print("\n" + "="*50)
print("Test chuẩn hóa tên class từ model (data.yaml format):")

# Model class names (từ data.yaml)
model_classes = [
    "Banh-beo",
    "Banh-canh",
    "Pho",
    "Bun-bo-Hue",
]

def normalize_food_key(class_name):
    """Chuẩn hóa tên class từ model để khớp với key trong food_data"""
    variations = [
        class_name,  # Trực tiếp
        class_name.replace('-', '_'),  # Thay gạch ngang bằng gạch dưới
        class_name.replace('_', '-'),  # Thay gạch dưới bằng gạch ngang
    ]
    
    for key in variations:
        if key in food_data:
            return key
    
    return class_name

print("\nTest chuẩn hóa:")
for class_name in model_classes:
    normalized = normalize_food_key(class_name)
    found = normalized in food_data
    print(f"  '{class_name}' -> '{normalized}' (Found: {found})")
    if found:
        print(f"    -> {food_data[normalized]['name_vi']}")
