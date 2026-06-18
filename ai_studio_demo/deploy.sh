#!/bin/bash
# Deploy the AI Function Studio Demo Streamlit app to Snowflake
set -e

cd "$(dirname "$0")/streamlit_app"

echo "Deploying AI Function Studio Demo app..."
snow streamlit deploy --replace --open

echo "Done. App deployed to AI_STUDIO_DEMO.PUBLIC.AI_STUDIO_DEMO_APP"
