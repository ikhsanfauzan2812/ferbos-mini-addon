# HACS Submission Information

## Repository Details
- **Name**: Ferbos Mini
- **GitHub URL**: https://github.com/ikhsanfauzan2812/ferbos-mini-addon
- **Category**: Integration
- **Description**: Home Assistant integration for database querying and configuration management

## HACS Configuration
- **hacs.json**: ✅ Created
- **manifest.json**: ✅ Updated with requirements
- **Documentation**: ✅ Comprehensive README
- **Code Quality**: ✅ Follows Home Assistant standards

## Integration Features
- Database querying via WebSocket API
- Configuration management (add lines to configuration.yaml)
- Secure API communication
- Real-time WebSocket communication
- Support for both legacy and modern API formats

## Prerequisites
- Requires Ferbos Mini add-on to be installed separately
- Home Assistant 2023.1.0+
- aiohttp>=3.8.0

## Installation Instructions for Users
1. Install via HACS (search "Ferbos Mini")
2. Install the Ferbos Mini add-on separately
3. Configure the integration with add-on URL
4. Start using WebSocket API commands

## Repository Structure
```
ferbos-mini-addon/
├── hacs.json
├── custom_components/
│   └── ferbos_mini/
│       ├── __init__.py
│       ├── api.py
│       ├── config_flow.py
│       ├── const.py
│       └── manifest.json
├── ferbos_addon_query/ (add-on files)
└── README_HACS.md
```

## Submission Checklist
- [x] Repository is public
- [x] hacs.json file present
- [x] manifest.json properly configured
- [x] Documentation complete
- [x] Integration follows HA standards
- [x] Requirements specified
- [x] Dependencies listed
- [x] Code owners specified
