# Test Code Blocks Document

## Python Examples

Here's a simple Python function:

```python
def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## JavaScript Code

Some JavaScript code:

```javascript
const fetchData = async (url) => {
    try {
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
    }
};
```

## Shell Scripts

A useful bash script:

```bash
#!/bin/bash
for file in *.md; do
    echo "Processing $file"
    wc -l "$file"
done
```

## YAML Configuration

```yaml
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
```

## No Language Specified

```
This is a code block without language specification.
It should still be captured.
```

## Inline Code

Don't forget about `inline code` examples like `print("hello")` or `const x = 42`.