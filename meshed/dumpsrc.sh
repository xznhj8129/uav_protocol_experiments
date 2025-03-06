#!/bin/bash
NAME="dump"
rm "./$NAME.txt"
touch "./$NAME.txt"

files=(
    node_uav.py
    node_controller.py
    protocol.py
    payload_enums.py
    message_structure.py
    message_definitions.json
    unavlib_example_mission.py
    unavlib_example_telemetry.py
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "$file"
    echo "# $file" >> "./$NAME.txt"
    echo "" >> "./$NAME.txt"
    echo '```' >> "./$NAME.txt"
    echo "" >> "./$NAME.txt"
    cat "$file" >> "./$NAME.txt"
    echo "" >> "./$NAME.txt"
    echo '```' >> "./$NAME.txt"
    echo "" >> "./$NAME.txt"
  else
    echo "File $file not found."
  fi
done

echo "Done! Check $NAME.txt for the output."
