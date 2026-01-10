#!/usr/bin/env python3
"""
Enhanced script to generate comprehensive OpenSpec specifications for all 37 pipeline steps.
Extracts information from multiple documentation sources and legacy code with proper prioritization.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class StepInfo:
    """Container for step specification information."""
    step_num: str
    purpose: str = ""
    business_context: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    key_features: List[str] = field(default_factory=list)
    performance_metrics: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    error_handling: List[str] = field(default_factory=list)
    thresholds: List[str] = field(default_factory=list)


def extract_docstring_from_python(filepath: str) -> Optional[Dict[str, str]]:
    """Extract module docstring and parse it for structured information from Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse with AST
        docstring = None
        try:
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)
        except:
            pass
        
        # Fallback: regex extraction for triple-quoted strings at file start
        if not docstring:
            pattern = r'^\s*["\']{{3}}(.*?)["\']{{3}}'
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                docstring = match.group(1).strip()
        
        if not docstring:
            return None
        
        # Parse docstring for structured information
        info = {'raw': docstring}
        
        # Extract purpose from first paragraph or title
        lines = docstring.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('=')]
        if non_empty_lines:
            # First non-empty line is often the title/purpose
            info['purpose'] = non_empty_lines[0]
            # Look for additional description in subsequent paragraphs
            desc_parts = []
            for line in non_empty_lines[1:5]:  # Take up to next 4 lines
                if line and not line.startswith('-') and not line.startswith('*'):
                    desc_parts.append(line)
            if desc_parts:
                info['description'] = ' '.join(desc_parts)
        
        # Extract inputs section
        input_match = re.search(r'(?:Inputs?|Input[s]? Files?|Dependencies):\s*(.*?)(?=\n\n|\n[A-Z]|$)', docstring, re.DOTALL | re.IGNORECASE)
        if input_match:
            info['inputs'] = input_match.group(1).strip()
        
        # Extract outputs section
        output_match = re.search(r'(?:Outputs?|Output Files?|Generates?):\s*(.*?)(?=\n\n|\n[A-Z]|$)', docstring, re.DOTALL | re.IGNORECASE)
        if output_match:
            info['outputs'] = output_match.group(1).strip()
        
        # Extract key features or capabilities
        features_match = re.search(r'(?:Key Features?|Capabilities|Features?):\s*(.*?)(?=\n\n|\n[A-Z]|$)', docstring, re.DOTALL | re.IGNORECASE)
        if features_match:
            info['features'] = features_match.group(1).strip()
        
        # Extract HOW TO RUN section if present
        howto_match = re.search(r'HOW TO RUN.*?:\s*(.*?)(?=\n\n[A-Z]|$)', docstring, re.DOTALL | re.IGNORECASE)
        if howto_match:
            info['howto'] = howto_match.group(1).strip()[:500]
        
        return info
        
    except Exception as e:
        print(f"Warning: Could not extract docstring from {filepath}: {e}")
        return None


def extract_from_markdown(filepath: str) -> Dict[str, str]:
    """Extract structured information from markdown documentation."""
    if not os.path.exists(filepath):
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        info = {}
        
        # Extract purpose/overview
        purpose_patterns = [
            r'##\s+Purpose\s*\n+(.*?)(?=\n##|\Z)',
            r'##\s+Overview\s*\n+(.*?)(?=\n##|\Z)',
            r'\*\*Purpose\*\*:?\s*(.*?)(?=\n|$)',
        ]
        for pattern in purpose_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                info['purpose'] = match.group(1).strip()[:500]
                break
        
        # Extract inputs
        input_patterns = [
            r'##\s+Input[s]?\s*\n+(.*?)(?=\n##|\Z)',
            r'\*\*Input[s]?\*\*:?\s*(.*?)(?=\n\*\*|\n##|\Z)',
        ]
        for pattern in input_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                info['inputs'] = match.group(1).strip()[:1000]
                break
        
        # Extract outputs
        output_patterns = [
            r'##\s+Output[s]?\s*\n+(.*?)(?=\n##|\Z)',
            r'\*\*Output[s]?\*\*:?\s*(.*?)(?=\n\*\*|\n##|\Z)',
        ]
        for pattern in output_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                info['outputs'] = match.group(1).strip()[:1000]
                break
        
        # Extract key features
        features_patterns = [
            r'##\s+Key Features?\s*\n+(.*?)(?=\n##|\Z)',
            r'\*\*Key Features?\*\*:?\s*(.*?)(?=\n\*\*|\n##|\Z)',
        ]
        for pattern in features_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                info['key_features'] = match.group(1).strip()[:1000]
                break
        
        # Extract performance
        perf_patterns = [
            r'##\s+Performance\s*\n+(.*?)(?=\n##|\Z)',
            r'\*\*Performance\*\*:?\s*(.*?)(?=\n\*\*|\n##|\Z)',
        ]
        for pattern in perf_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                info['performance'] = match.group(1).strip()[:500]
                break
        
        # Extract dependencies
        dep_patterns = [
            r'##\s+Dependencies\s*\n+(.*?)(?=\n##|\Z)',
            r'\*\*Dependencies\*\*:?\s*(.*?)(?=\n\*\*|\n##|\Z)',
        ]
        for pattern in dep_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                info['dependencies'] = match.group(1).strip()[:500]
                break
        
        return info
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return {}


def parse_list_items(text: str) -> List[str]:
    """Parse markdown list items from text."""
    if not text:
        return []
    
    items = []
    lines = text.split('\n')
    for line in lines:
        # Match bullet points or numbered lists
        match = re.match(r'^\s*[-*•]\s+(.*)', line)
        if match:
            items.append(match.group(1).strip())
        else:
            match = re.match(r'^\s*\d+\.\s+(.*)', line)
            if match:
                items.append(match.group(1).strip())
    
    return items if items else [text.strip()]


def gather_step_info(step_num: str) -> StepInfo:
    """Gather comprehensive information for a step from all sources."""
    info = StepInfo(step_num=step_num)
    
    # Source priority: code (PRIMARY) > archive_docs/ > fortification/
    # Code has highest priority because it represents actual implementation
    sources = []
    
    step_number = step_num.replace('step', '').replace('0', '', 1) if step_num.startswith('step0') else step_num.replace('step', '')
    
    # PRIMARY: Legacy code (actual implementation)
    legacy_patterns = [
        f"src/step{step_number.zfill(2)}_*.py",
        f"src/step{step_number}_*.py",
    ]
    for pattern in legacy_patterns:
        import glob
        for filepath in glob.glob(pattern):
            sources.append(('code', filepath))
    
    # SECONDARY: archive_docs/docs/ (historical documentation)
    archive_paths = [
        f"archive_docs/docs/step{step_number.zfill(2)}_*.md",
        f"archive_docs/docs/steps/step{step_number}_*.md",
    ]
    
    for pattern in archive_paths:
        import glob
        for filepath in glob.glob(pattern):
            sources.append(('archive', filepath))
    
    # TERTIARY: docs/fortification/steps/ (secondary documentation)
    fort_path = f"docs/fortification/steps/step{step_number.zfill(2)}_fortified.md"
    if os.path.exists(fort_path):
        sources.append(('fortification', fort_path))
    
    # FALLBACK: Comprehensive pipeline doc (only if nothing else found)
    sources.append(('archive_fallback', 'archive_docs/docs/COMPLETE_PIPELINE_DOCUMENTATION.md'))
    
    # Extract from all sources
    for source_type, filepath in sources:
        # Skip fallback if we already have a purpose
        if source_type == 'archive_fallback' and info.purpose:
            continue
            
        if source_type == 'code':
            code_info = extract_docstring_from_python(filepath)
            if code_info:
                # Parse docstring for purpose (prioritize actual code implementation)
                if code_info.get('purpose') and not info.purpose:
                    purpose_text = code_info['purpose']
                    # Clean up step number prefix if present
                    purpose_text = re.sub(r'^Step\s+\d+[AB]?:\s*', '', purpose_text, flags=re.IGNORECASE)
                    info.purpose = purpose_text[:500]
                elif code_info.get('description') and not info.purpose:
                    info.purpose = code_info['description'][:500]
                
                # Extract inputs from code
                if code_info.get('inputs'):
                    items = parse_list_items(code_info['inputs'])
                    info.inputs.extend([item for item in items if item not in info.inputs])
                
                # Extract outputs from code
                if code_info.get('outputs'):
                    items = parse_list_items(code_info['outputs'])
                    info.outputs.extend([item for item in items if item not in info.outputs])
                
                # Extract features from code
                if code_info.get('features'):
                    items = parse_list_items(code_info['features'])
                    info.key_features.extend([item for item in items if item not in info.key_features])
        else:
            doc_info = extract_from_markdown(filepath)
            
            # Merge with priority (markdown docs have lower priority than code)
            if doc_info.get('purpose') and not info.purpose:
                purpose_text = doc_info['purpose']
                # Clean up common prefixes
                purpose_text = re.sub(r'^Step\s+\d+[AB]?:\s*', '', purpose_text, flags=re.IGNORECASE)
                purpose_text = re.sub(r'^\*\*Purpose\*\*:?\s*', '', purpose_text, flags=re.IGNORECASE)
                info.purpose = purpose_text[:500]
            
            if doc_info.get('inputs'):
                items = parse_list_items(doc_info['inputs'])
                info.inputs.extend([item for item in items if item not in info.inputs])
            
            if doc_info.get('outputs'):
                items = parse_list_items(doc_info['outputs'])
                info.outputs.extend([item for item in items if item not in info.outputs])
            
            if doc_info.get('key_features'):
                items = parse_list_items(doc_info['key_features'])
                info.key_features.extend([item for item in items if item not in info.key_features])
            
            if doc_info.get('performance'):
                items = parse_list_items(doc_info['performance'])
                info.performance_metrics.extend([item for item in items if item not in info.performance_metrics])
            
            if doc_info.get('dependencies'):
                items = parse_list_items(doc_info['dependencies'])
                info.dependencies.extend([item for item in items if item not in info.dependencies])
    
    return info


def create_comprehensive_spec(info: StepInfo) -> str:
    """Create comprehensive OpenSpec specification from gathered information."""
    
    # Determine step name
    step_number = info.step_num.replace('step', '')
    if info.step_num == "step02b":
        step_title = "Step 2B: Seasonal Data Consolidation"
    elif step_number.isdigit():
        step_title = f"Step {int(step_number)}"
    else:
        step_title = f"Step {step_number}"
    
    # Build specification
    spec = f"""# {step_title} Capability Specification

## Purpose

{info.purpose if info.purpose else f"Step {step_number} provides specialized processing for the Product Mix Clustering pipeline."}

## Requirements

"""
    
    # Requirement 1: Core Functionality
    spec += f"""### Requirement: Core Functionality
The system SHALL execute {step_title.lower()} processing with all required transformations and business logic.

#### Scenario: Primary operation execution
- **GIVEN** valid input data and configuration
- **WHEN** {step_title} processing executes
- **THEN** all required outputs are generated successfully
- **AND** data quality standards are maintained throughout processing
- **AND** processing completes within performance requirements

"""
    
    # Requirement 2: Input/Output Management (if we have details)
    if info.inputs or info.outputs:
        spec += """### Requirement: Input and Output Management
The system SHALL manage inputs and outputs with proper validation and formatting.

"""
        if info.inputs:
            spec += f"""#### Scenario: Input validation and processing
- **GIVEN** upstream data dependencies are satisfied
- **WHEN** input data is loaded
- **THEN** input data structure is validated
- **AND** required fields are present and properly formatted
- **AND** data completeness meets minimum thresholds

"""
        
        if info.outputs:
            spec += f"""#### Scenario: Output generation and persistence
- **GIVEN** processing has completed successfully
- **WHEN** outputs are generated
- **THEN** output files are created with correct structure
- **AND** output data passes validation checks
- **AND** outputs are persisted to appropriate directories

"""
    
    # Requirement 3: Key Features Implementation (if we have features)
    if info.key_features:
        spec += """### Requirement: Key Features Implementation
The system SHALL implement all key features required for comprehensive analysis.

#### Scenario: Feature execution
- **GIVEN** feature requirements are defined
- **WHEN** key features execute
- **THEN** all documented features operate correctly
- **AND** feature outputs meet business requirements
- **AND** features integrate properly with pipeline

"""
    
    # Requirement 4: Data Quality and Validation
    spec += """### Requirement: Data Quality and Validation
The system SHALL maintain data quality through comprehensive validation.

#### Scenario: Data quality checks
- **GIVEN** data at various processing stages
- **WHEN** quality validation occurs
- **THEN** data completeness is verified
- **AND** data consistency is validated
- **AND** data accuracy meets business requirements
- **AND** quality issues are logged and reported

"""
    
    # Requirement 5: Error Handling and Recovery
    spec += """### Requirement: Error Handling and Recovery
The system SHALL provide robust error handling and recovery mechanisms for production reliability.

#### Scenario: Error detection and handling
- **GIVEN** various failure modes during execution
- **WHEN** errors occur
- **THEN** errors are detected and logged with full context
- **AND** appropriate recovery actions are initiated
- **AND** partial results are preserved when possible
- **AND** error notifications include actionable information

"""
    
    # Requirement 6: Performance and Scalability
    if info.performance_metrics:
        spec += """### Requirement: Performance and Scalability Standards
The system SHALL meet performance standards for production deployment with large datasets.

#### Scenario: Performance validation
- **GIVEN** standard production datasets
- **WHEN** processing executes
- **THEN** execution time meets specified targets
- **AND** memory usage scales appropriately with data volume
- **AND** processing throughput maintains acceptable rates
- **AND** resource utilization remains efficient

"""
    else:
        spec += """### Requirement: Performance Standards
The system SHALL meet performance standards for production deployment.

#### Scenario: Performance compliance
- **GIVEN** production workload requirements
- **WHEN** step executes
- **THEN** processing completes within acceptable timeframes
- **AND** resource usage remains within defined limits
- **AND** performance degrades gracefully under load

"""
    
    # Requirement 7: Integration and Dependencies (if we have dependencies)
    if info.dependencies:
        spec += """### Requirement: Pipeline Integration and Dependencies
The system SHALL integrate properly with upstream and downstream pipeline components.

#### Scenario: Dependency management
- **GIVEN** pipeline execution context
- **WHEN** step initializes
- **THEN** all required dependencies are available
- **AND** dependency versions are compatible
- **AND** upstream outputs are in expected format
- **AND** downstream consumers can process outputs

"""
    
    return spec


def main():
    """Generate comprehensive specifications for all 37 steps."""
    print("Generating comprehensive OpenSpec specifications for all 37 pipeline steps...")
    print("=" * 80)
    
    # Generate specs for all steps
    all_steps = []
    
    # Steps 1-19 (core pipeline)
    all_steps.extend([f"step{i:02d}" for i in range(1, 20)])
    # Add step02b
    all_steps.append("step02b")
    # Steps 20-37 (advanced analysis)
    all_steps.extend([f"step{i:02d}" for i in range(20, 38)])
    # Add step34a and step34b
    all_steps.extend(["step34a", "step34b"])
    
    # Remove duplicates and sort
    all_steps = sorted(set(all_steps))
    
    created_count = 0
    failed_count = 0
    
    for step_num in all_steps:
        try:
            print(f"\nProcessing {step_num}...")
            
            # Gather information from all sources
            info = gather_step_info(step_num)
            
            # Create specification
            spec_content = create_comprehensive_spec(info)
            
            # Write to file
            spec_dir = f"openspec/specs/{step_num}"
            os.makedirs(spec_dir, exist_ok=True)
            spec_path = os.path.join(spec_dir, "spec.md")
            
            with open(spec_path, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            print(f"  ✓ Created {spec_path}")
            print(f"    - Purpose: {info.purpose[:80] if info.purpose else 'N/A'}...")
            print(f"    - Inputs: {len(info.inputs)} items")
            print(f"    - Outputs: {len(info.outputs)} items")
            print(f"    - Features: {len(info.key_features)} items")
            
            created_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed to create {step_num}: {e}")
            failed_count += 1
    
    print("\n" + "=" * 80)
    print(f"Summary: Created {created_count} specifications, {failed_count} failures")
    print(f"Next: Run 'openspec validate --strict' to validate all specifications")


if __name__ == "__main__":
    main()
