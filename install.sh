#!/bin/bash
# Ferbos Mini Integration Installer

echo "Installing Ferbos Mini Integration..."

# Get Home Assistant config directory
if [ -z "$HA_CONFIG" ]; then
    HA_CONFIG="/config"
fi

# Create custom_components directory if it doesn't exist
mkdir -p "$HA_CONFIG/custom_components"

# Download the integration
echo "Downloading Ferbos Mini integration..."
curl -L -o ferbos_mini.zip https://github.com/ikhsanfauzan2812/ferbos-mini-addon/archive/main.zip

# Extract the integration
unzip -q ferbos_mini.zip
cp -r ferbos-mini-addon-main/custom_components/ferbos_mini "$HA_CONFIG/custom_components/"

# Clean up
rm -rf ferbos_mini.zip ferbos-mini-addon-main

echo "✅ Ferbos Mini integration installed successfully!"
echo "Please restart Home Assistant and add the integration via Settings > Devices & Services"
