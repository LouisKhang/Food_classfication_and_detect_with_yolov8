# Contributing to Food Detection System

Thank you for your interest in contributing! This document provides guidelines for contributing to the Vietnamese Food Detection project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:
- Be respectful and professional
- Welcome diverse perspectives
- Focus on constructive feedback
- Report inappropriate behavior

---

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- Virtual environment (recommended)
- Basic knowledge of YOLOv8 and object detection

### Fork & Clone
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/yourusername/food_detection.git
cd food_selected_pho_bun

# Add upstream remote
git remote add upstream https://github.com/originalrepo/food_detection.git
```

### Setup Development Environment
```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest flake8 black
```

---

## How to Contribute

### Areas for Contribution

#### 1. **Bug Fixes**
- Report bugs via GitHub Issues
- Include reproduction steps
- Test your fix thoroughly
- Submit pull request with fix

#### 2. **Feature Development**
- Extend food classes
- Improve accuracy/performance
- Add new payment methods
- Enhance UI/UX
- Add multi-language support
- Implement mobile app

#### 3. **Documentation**
- Improve README files
- Add code comments
- Create tutorials
- Update API documentation
- Translate to other languages

#### 4. **Testing**
- Write unit tests
- Add integration tests
- Improve test coverage
- Test on different platforms

#### 5. **Data Collection**
- Contribute food images
- Annotate datasets
- Improve dataset quality
- Expand food categories

#### 6. **Performance Optimization**
- Reduce inference time
- Lower memory usage
- Optimize model size
- Improve FPS

---

## Development Setup

### Project Structure
```
food_selected_pho_bun/
├── app/                    # Application code
│   ├── main.py
│   ├── main_window.py
│   ├── result_screen.py
│   ├── yolo_model.py
│   ├── config.py
│   └── ...
├── dataset/               # Training data
├── tests/                 # Test files (to be created)
├── requirements.txt       # Dependencies
└── README.md             # Documentation
```

### Creating a Feature Branch
```bash
# Update main branch
git fetch upstream
git rebase upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

---

## 📝 Coding Standards

### Python Style Guide
Follow PEP 8:
- 4-space indentation
- Max line length: 100 characters
- Use meaningful variable names
- Document functions with docstrings

### Docstring Format
```python
def detect_food(image, confidence=0.5):
    """
    Detect food items in an image using YOLOv8.
    
    Args:
        image (np.ndarray): Input image in BGR format
        confidence (float): Detection confidence threshold (0.0-1.0)
        
    Returns:
        list: Detected objects with bounding boxes and confidence scores
        
    Example:
        >>> detections = detect_food(image, confidence=0.5)
        >>> for detection in detections:
        >>>     print(detection['name'], detection['confidence'])
    """
    pass
```

### Comments
```python
# Use clear, concise comments
# Explain WHY, not WHAT
# Bad: i = i + 1  # increment i
# Good: user_count += 1  # track number of processed users
```

### Imports
```python
# Order: standard library, third-party, local
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import MODEL_PATH
from app.image_utils import resize_image
```

### Code Formatting
```bash
# Format code with black
black app/

# Check style with flake8
flake8 app/ --max-line-length=100

# Sort imports
isort app/
```

---

## 📌 Commit Guidelines

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation
- **style**: Formatting
- **refactor**: Code restructuring
- **perf**: Performance improvement
- **test**: Adding tests
- **chore**: Maintenance

### Examples
```
feat(detection): add confidence slider to main window
fix(model): handle missing model file gracefully
docs(readme): add installation instructions
perf(inference): optimize image preprocessing
test(payment): add payment system unit tests
```

### Commit Best Practices
- Commit related changes together
- Write descriptive messages
- Keep commits atomic (one change per commit)
- Reference issues: "fixes #123"
- Use present tense: "add feature" not "added feature"

---

## 🔄 Pull Request Process

### Before Submitting
1. Update your branch with latest upstream
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Test your changes
   ```bash
   # Run tests
   pytest tests/
   
   # Check code style
   flake8 app/
   black app/ --check
   ```

3. Update documentation
   - Update README if needed
   - Add docstrings
   - Update UPDATES.md

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Performance improvement

## Related Issues
Closes #(issue number)

## Testing
- [ ] Tested on Windows
- [ ] Tested on macOS
- [ ] Tested on Linux
- [ ] All tests pass

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Comments added
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added/updated
```

### Review Process
- Maintainers will review within 1 week
- Address review comments
- Re-request review when updated
- Maintainers merge when approved

---

## 🐛 Reporting Bugs

### Before Reporting
- Search existing issues
- Check documentation
- Verify it's not a configuration issue

### Bug Report Template
```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: Windows/macOS/Linux
- Python Version: 3.8/3.9/3.10/3.11
- Dependencies: (output of pip list)
- Camera/Hardware: (if relevant)

## Error Messages
```
Paste error traceback here
```

## Screenshots
Add screenshots if helpful

## Additional Context
Any other relevant information
```

---

## 💭 Feature Requests

### Before Requesting
- Check existing issues and discussions
- Verify it aligns with project goals

### Feature Request Template
```markdown
## Feature Description
Clear description of desired feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives
Any alternative approaches?

## Additional Context
Examples, mockups, related issues
```

---

## 🧪 Testing

### Writing Tests
```python
# Example test file: tests/test_yolo_model.py
import pytest
from app.yolo_model import YOLOModel

class TestYOLOModel:
    @pytest.fixture
    def model(self):
        return YOLOModel(model_path="path/to/model.pt")
    
    def test_model_initialization(self, model):
        assert model is not None
        assert model.model is not None
    
    def test_detection(self, model, sample_image):
        results = model.predict(sample_image)
        assert isinstance(results, list)
        assert len(results) > 0
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_yolo_model.py

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_yolo_model.py::TestYOLOModel::test_detection
```

---

## Documentation Contributions

### Updating README
- Keep it clear and concise
- Add examples
- Update table of contents
- Fix broken links

### Adding Tutorials
- Use clear step-by-step format
- Include code examples
- Add screenshots/diagrams
- Test all instructions

### Translation
- Translate to new languages
- Keep meaning and tone
- Use consistent terminology
- Update file names (e.g., README_zh.md)

---

## Learning Resources

### YOLOv8 Documentation
- https://docs.ultralytics.com/
- https://github.com/ultralytics/ultralytics

### Object Detection
- https://arxiv.org/abs/2301.11799 (YOLOv8 paper)
- https://www.deeplearning.ai/ (Deep Learning courses)

### Python Best Practices
- https://pep8.org/
- https://www.python.org/dev/peps/pep-0257/ (Docstrings)

### Git & GitHub
- https://git-scm.com/doc
- https://docs.github.com/

---

## Questions?

- Check existing issues and discussions
- Create a GitHub Discussion
- Contact maintainers
- Join community forums

---

## Recognition

We recognize and appreciate all contributors! Your contributions will be:
- Credited in project
- Mentioned in release notes
- Added to contributors list

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to the Vietnamese Food Detection System!**

**Last Updated**: January 28, 2026  
**Version**: 1.0
