#!/usr/bin/env bash

# Remove set -e to allow the script to continue even if some conversions fail
# set -e

# Logging function
log() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message"
}

# Check if ImageMagick is installed
check_dependencies() {
    if ! command -v convert &> /dev/null; then
        log "ERROR" "ImageMagick is not installed. Please install it first."
        log "INFO" "On Fedora, you can install it using: sudo dnf install ImageMagick"
        exit 1
    fi
}

# Convert SVG to PNG
convert_svg_to_png() {
    local svg_file="$1"
    local png_file="${svg_file%.svg}.png"
    
    if [ ! -f "$svg_file" ]; then
        log "ERROR" "SVG file not found: $svg_file"
        return 1
    fi
    
    log "INFO" "Converting $svg_file to PNG..."
    if convert -background none -density 300 "$svg_file" "$png_file"; then
        log "INFO" "Successfully converted $svg_file to $png_file"
        return 0
    else
        log "ERROR" "Failed to convert $svg_file"
        return 1
    fi
}

# Process directory
process_directory() {
    local dir="$1"
    local count=0
    local failed=0
    local total=0
    
    if [ ! -d "$dir" ]; then
        log "ERROR" "Directory not found: $dir"
        exit 1
    fi
    
    log "INFO" "Processing directory: $dir"
    
    # Count total SVG files first
    total=$(find "$dir" -type f -name "*.svg" | wc -l)
    log "INFO" "Found $total SVG files to process"
    
    # Find all SVG files in the directory and subdirectories
    while IFS= read -r -d '' file; do
        if convert_svg_to_png "$file"; then
            ((count++))
        else
            ((failed++))
        fi
    done < <(find "$dir" -type f -name "*.svg" -print0)
    
    log "INFO" "Conversion complete: $count files converted successfully, $failed files failed out of $total total files"
    
    if [ $failed -gt 0 ]; then
        return 1
    fi
    return 0
}

# Show usage
show_usage() {
    echo "Usage: $0 <directory>"
    echo "Convert all SVG files in the specified directory and its subdirectories to PNG format."
    echo
    echo "Arguments:"
    echo "  directory    Path to the directory containing SVG files"
    echo
    echo "Example:"
    echo "  $0 ./docs"
    exit 1
}

# Main function
main() {
    if [ $# -ne 1 ]; then
        show_usage
    fi
    
    local dir="$1"
    
    check_dependencies
    process_directory "$dir"
}

# Execute main function
main "$@" 