import os
import json

# Define mappings for property names across different build.prop files
PROPERTY_VARIATIONS = {
    "MANUFACTURER": ["ro.product.system.manufacturer", "ro.product.vendor.manufacturer", "ro.product.product.manufacturer", "ro.product.manufacturer"],
    "MODEL": ["ro.product.system.model", "ro.product.vendor.model", "ro.product.product.model", "ro.product.model"],
    "FINGERPRINT": ["ro.system.build.fingerprint", "ro.build.fingerprint", "ro.product.build.fingerprint", "ro.vendor.build.fingerprint"],
    "BRAND": ["ro.product.system.brand", "ro.product.vendor.brand", "ro.product.product.brand", "ro.product.brand"],
    "PRODUCT": ["ro.product.system.name", "ro.product.vendor.name", "ro.product.product.name", "ro.product.name"],
    "DEVICE": ["ro.product.system.device", "ro.product.vendor.device", "ro.product.product.device", "ro.product.device"],
    "RELEASE": ["ro.system.build.version.release", "ro.build.version.release", "ro.product.build.version.release", "ro.vendor.build.version.release"],
    "ID": ["ro.system.build.id", "ro.build.id", "ro.product.build.id", "ro.vendor.build.id"],
    "INCREMENTAL": ["ro.system.build.version.incremental", "ro.build.version.incremental", "ro.product.build.version.incremental", "ro.vendor.build.version.incremental"],
    "TYPE": ["ro.system.build.type", "ro.build.type", "ro.product.build.type", "ro.vendor.build.type"],
    "TAGS": ["ro.system.build.tags", "ro.build.tags", "ro.product.build.tags", "ro.vendor.build.tags"],
    "SECURITY_PATCH": ["ro.system.build.version.security_patch", "ro.build.version.security_patch", "ro.product.build.version.security_patch", "ro.vendor.build.version.security_patch"],
    "DEVICE_INITIAL_SDK_INT": ["ro.system.build.version.sdk", "ro.build.version.sdk", "ro.product.build.version.sdk", "ro.vendor.build.version.sdk"]
}

def item(msg):
    print("\n- " + msg)

def file_getprop(filepath, prop):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith(prop):
                    return line.split('=')[1].strip()
    except (IOError, OSError) as e:
        print(f"Error while reading {filepath}: {e}")
    return None

def extract_properties(build_prop_files):
    properties = {}
    system_build_prop_found = False
    for build_prop_file in build_prop_files:
        if "_system_build.prop" in build_prop_file:
            system_build_prop_found = True
            properties = extract_properties_from_file(build_prop_file)
            break

    if not system_build_prop_found:
        for build_prop_file in build_prop_files:
            properties.update(extract_properties_from_file(build_prop_file))
    
    # If FINGERPRINT not found, generate it from required properties
    if "FINGERPRINT" not in properties:
        fingerprint = generate_fingerprint(properties)
        if fingerprint:
            properties["FINGERPRINT"] = fingerprint

    return properties

def extract_properties_from_file(build_prop_file):
    properties = {}
    for prop_key, prop_variations in PROPERTY_VARIATIONS.items():
        prop_value = None
        for prop_var in prop_variations:
            prop_value = file_getprop(build_prop_file, prop_var)
            if prop_value:
                properties[prop_key] = prop_value
                break
    return properties

def generate_fingerprint(properties):
    required_properties = ["BRAND", "PRODUCT", "DEVICE", "RELEASE", "ID", "INCREMENTAL", "TYPE", "TAGS"]
    if not all(prop_key in properties for prop_key in required_properties):
        return None

    fingerprint = f"{properties['BRAND']}/{properties['PRODUCT']}/{properties['DEVICE']}:{properties['RELEASE']}/{properties['ID']}/{properties['INCREMENTAL']}:{properties['TYPE']}/{properties['TAGS']}"
    return fingerprint

def main():
    print("Android Build.prop to Custom.pif.json Creator")
    print("by FrogMaster- @ xda-developers")

    for manufacturer in os.listdir('.'):
        if not os.path.isdir(manufacturer):
            continue

        item(f"Manufacturer: {manufacturer}")
        manufacturer_dir = os.path.join('.', manufacturer)

        # Dictionary to store properties for each firmware
        firmware_properties = {}

        # Search for relevant build.prop files
        for filename in os.listdir(manufacturer_dir):
            if filename.endswith("_system_build.prop") or \
               filename.endswith("_vendor_build.prop") or \
               filename.endswith("_product_build.prop") or \
               filename.endswith("_build.prop"):

                # Extract firmware name from the first encountered build.prop filename
                firmware_name = os.path.splitext(filename)[0]
                firmware_name = firmware_name.replace("_system_build", "").replace("_vendor_build", "").replace("_product_build", "").replace("_build", "")
                
                # Initialize properties for the firmware if not already present
                if firmware_name not in firmware_properties:
                    firmware_properties[firmware_name] = {}

                filepath = os.path.join(manufacturer_dir, filename)
                properties = extract_properties([filepath])

                # Update properties for the firmware
                firmware_properties[firmware_name].update(properties)

        # Process properties for each firmware
        for firmware_name, properties in firmware_properties.items():
            # Add additional values
            properties["*.build.id"] = properties.get("ID", "")
            properties["*.security_patch"] = properties.get("SECURITY_PATCH", "")
            properties["*api_level"] = properties.get("DEVICE_INITIAL_SDK_INT", "")

            # Reorder properties
            reordered_properties = {
                "MANUFACTURER": properties.get("MANUFACTURER", ""),
                "MODEL": properties.get("MODEL", ""),
                "FINGERPRINT": properties.get("FINGERPRINT", ""),
                "BRAND": properties.get("BRAND", ""),
                "PRODUCT": properties.get("PRODUCT", ""),
                "DEVICE": properties.get("DEVICE", ""),
                "RELEASE": properties.get("RELEASE", ""),
                "ID": properties.get("ID", ""),
                "INCREMENTAL": properties.get("INCREMENTAL", ""),
                "TYPE": properties.get("TYPE", ""),
                "TAGS": properties.get("TAGS", ""),
                "SECURITY_PATCH": properties.get("SECURITY_PATCH", ""),
                "DEVICE_INITIAL_SDK_INT": properties.get("DEVICE_INITIAL_SDK_INT", ""),
                "*.build.id": properties.get("ID", ""),
                "*.security_patch": properties.get("SECURITY_PATCH", ""),
                "*api_level": properties.get("DEVICE_INITIAL_SDK_INT", "")
            }

            custom_pif_filepath = os.path.join(manufacturer_dir, f"{firmware_name}_custom.pif.json")
            if os.path.exists(custom_pif_filepath):
                item(f"Removing existing {custom_pif_filepath} ...")
                os.remove(custom_pif_filepath)

            item(f"Generating {custom_pif_filepath} ...")
            write_custom_pif_json(custom_pif_filepath, reordered_properties)

def write_custom_pif_json(filepath, properties):
    with open(filepath, 'w') as f:
        json.dump(properties, f, indent=4)

if __name__ == "__main__":
    main()
