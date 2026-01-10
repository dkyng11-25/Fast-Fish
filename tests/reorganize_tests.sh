#!/bin/bash
# Reorganize all step tests into step##/ directories

# Create all step directories
for i in {1..36}; do
    mkdir -p "step$(printf "%02d" $i)"
done

# Also create step2b directory
mkdir -p step2b

# Move all test files to their respective directories
for file in test_step*.py; do
    if [ -f "$file" ]; then
        # Extract step number from filename
        if [[ $file =~ test_step([0-9]+) ]]; then
            step_num="${BASH_REMATCH[1]}"
            step_dir="step$(printf "%02d" $step_num)"
            echo "Moving $file to $step_dir/"
            mv "$file" "$step_dir/"
        elif [[ $file =~ test_step2b ]]; then
            echo "Moving $file to step2b/"
            mv "$file" "step2b/"
        fi
    fi
done

# Move existing synthetic test directories into main step directories
for dir in step*_synthetic/; do
    if [ -d "$dir" ]; then
        base=$(echo "$dir" | sed 's/_synthetic\///')
        if [ "$base" = "step2b" ]; then
            target="step2b"
        else
            # Extract number and format
            num=$(echo "$base" | sed 's/step//')
            target="step$(printf "%02d" $num)"
        fi
        echo "Moving contents of $dir to $target/"
        mv "$dir"/* "$target/" 2>/dev/null
        rmdir "$dir" 2>/dev/null
    fi
done

# Move dual_output_synthetic contents to appropriate step directories
if [ -d "dual_output_synthetic" ]; then
    for file in dual_output_synthetic/test_step*.py; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            if [[ $filename =~ test_step([0-9]+) ]]; then
                step_num="${BASH_REMATCH[1]}"
                step_dir="step$(printf "%02d" $step_num)"
                echo "Moving $file to $step_dir/"
                mv "$file" "$step_dir/"
            elif [[ $filename =~ test_step2b ]]; then
                echo "Moving $file to step2b/"
                mv "$file" "step2b/"
            fi
        fi
    done
fi

echo "Reorganization complete!"
