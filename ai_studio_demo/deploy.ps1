# Deploy the AI Function Studio Demo Streamlit app to Snowflake
$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\streamlit_app"

Write-Host "Deploying AI Function Studio Demo app..."
snow streamlit deploy --replace --open

Pop-Location

Write-Host "Done. App deployed to AI_STUDIO_DEMO.PUBLIC.AI_STUDIO_DEMO_APP"
