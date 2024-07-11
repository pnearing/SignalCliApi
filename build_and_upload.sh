#!/bin/bash
rm -rf dist/*

python3 -m build
if [ $? -gt 0 ]; then
	echo "Build failed. Abort."
	exit 1
fi
exec python3 -m twine upload --repository SignalCliApi dist/*
