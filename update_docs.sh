#!/bin/bash

echo "Removing docs/html/"
rm -rf docs/html
echo "Creating documentation..."
pdoc --footer-text 'Version 1.0' \
--output-directory 'docs/html/' \
src/signal_cli_api/
echo "Complete."
