# Quick Start Guide - Product Mix Clustering Pipeline

## 🚀 Get Started in 3 Steps

### 1. Setup & Installation
```bash
# Clone and navigate to project
cd ProducMixClustering_pipeline

# Install dependencies  
pip install -r requirements.txt

# Verify setup
python pipeline.py --help
```

### 2. Run Complete Pipeline
```bash
# Execute full 15-step pipeline for June 2025 First Half
python pipeline.py --month 202506 --period A --validate-data
```

### 3. View Results
Open the generated dashboards in your browser:
- `output/global_overview_spu_dashboard.html` - Executive dashboard
- `output/interactive_map_spu_dashboard.html` - Geographic visualization

## ⚡ Common Commands

### Basic Execution
```bash
# Full pipeline with validation (recommended)
python pipeline.py --month 202506 --period A --validate-data

# Full pipeline without validation (faster)  
python pipeline.py --month 202506 --period A

# Clear previous data and restart
python pipeline.py --month 202506 --period A --clear-period --validate-data
```

### Step Control
```bash
# Run only business rules (after data collection is complete)
python pipeline.py --month 202506 --period A --start-step 7 --end-step 12

# Run only dashboards (after rules are complete)
python pipeline.py --month 202506 --period A --start-step 13 --end-step 15

# List all available steps
python pipeline.py --list-steps
```

### Error Handling
```bash
# Debug mode (stops on any error)
python pipeline.py --month 202506 --period A --strict --validate-data

# Check available periods
python pipeline.py --list-periods
```

## 📊 What You'll Get

### Key Output Files
| File | Description | Size |
|------|-------------|------|
| `consolidated_rule_results.csv` | Main analysis results | 2.3MB |
| `global_overview_spu_dashboard.html` | Executive dashboard | 11KB |
| `interactive_map_spu_dashboard.html` | Geographic visualization | 7.1MB |
| `clustering_results.csv` | Store cluster assignments | 19KB |

### Business Rules Results
| Rule | Purpose | Typical Results |
|------|---------|-----------------|
| 7 | Missing Categories | 1,611 stores, 3,878 opportunities |
| 8 | Imbalanced Allocation | 2,254 stores, 43,170 cases |
| 9 | Below Minimum | 2,263 stores, 54,698 cases |
| 10 | Smart Overcapacity | 601 stores, 1,219 cases |
| 11 | Missed Sales | 0 stores (no issues found) |
| 12 | Sales Performance | 1,326 stores with opportunities |

## ⏱️ Expected Timeline

### Complete Pipeline (Steps 1-15)
- **Total Time**: ~65 minutes
- **Critical Path**: API Download (15 min) + Temperature Calc (14 min) + Business Rules (35 min)
- **Success Rate**: 100% with proper setup

### Step Breakdown
| Phase | Steps | Time | Critical |
|-------|-------|------|----------|
| Data Collection | 1-3 | ~16 min | ✅ Yes |
| Weather Integration | 4-5 | ~14 min | ❌ No |
| Clustering | 6 | <1 min | ✅ Yes |
| Business Rules | 7-12 | ~35 min | ❌ No |
| Dashboards | 13-15 | <1 min | ❌ No |

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. Memory Issues
```bash
# Check available RAM (need 32GB+)
# Close other applications
# Monitor with task manager during execution
```

#### 2. API Timeout Errors
```bash
# Check internet connection
# Pipeline has automatic retry logic
# If persistent, contact API support
```

#### 3. Missing Files Error
```bash
# Clear and restart
python pipeline.py --month 202506 --period A --clear-period --validate-data
```

#### 4. Permission Errors
```bash
# Ensure write access to data/ and output/ directories
chmod -R 755 data/ output/
```

### Debug Mode
```bash
# Enable detailed error reporting
python pipeline.py --month 202506 --period A --strict --validate-data
```

## 🎯 Next Steps

### After First Run
1. **Explore Dashboards**: Open HTML files in browser
2. **Analyze Results**: Review `consolidated_rule_results.csv`
3. **Deep Dive**: Examine individual rule result files
4. **Geographic Analysis**: Use interactive map for regional insights

### Advanced Usage
```bash
# Run for different periods
python pipeline.py --month 202507 --period A  # July first half
python pipeline.py --month 202507 --period B  # July second half

# Skip steps for testing
python pipeline.py --month 202506 --period A --start-step 7  # Skip data collection
```

### Integration
- Import CSV results into BI tools
- Schedule regular pipeline execution
- Customize business rule thresholds
- Add additional visualization layers

## 📚 Additional Resources

- **Complete Documentation**: `docs/COMPLETE_PIPELINE_DOCUMENTATION.md`
- **Step Reference**: `docs/PIPELINE_STEPS_REFERENCE.md`
- **Configuration Guide**: See `config.py` inline documentation
- **API Documentation**: `docs/API.md`

## 🆘 Getting Help

### Self-Service
1. Check this guide for common issues
2. Review error logs with timestamps
3. Use `--strict` mode for detailed debugging
4. Verify system requirements (32GB+ RAM, Python 3.12+)

### Support Escalation
- Review complete documentation in `docs/`
- Contact development team with error logs
- Include system specifications and command used
- Specify which step failed and error message

---

**🎉 Ready to optimize your product mix? Run the pipeline and explore the insights!**

*Total setup time: <5 minutes | First run time: ~65 minutes | Ongoing runs: ~65 minutes* 