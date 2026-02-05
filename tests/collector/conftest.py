"""Fixtures for collector tests."""

import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_html_real_estate():
    """Sample HTML content for real estate website."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Luxury Properties - Find Your Dream Home</title>
        <meta name="description" content="Browse luxury apartments and villas for sale">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <nav>
            <a href="/">Home</a>
            <a href="/properties">Properties</a>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
        </nav>
        <h1>Find Your Perfect Property</h1>
        <h2>Featured Listings</h2>
        <div class="property">
            <h3>3 Bedroom Villa - $500,000</h3>
            <p>2000 sqft, modern floor plan</p>
            <a href="/inquiry" class="cta">Inquire Now</a>
        </div>
        <a href="https://wa.me/1234567890" class="whatsapp">Contact via WhatsApp</a>
        <form action="/contact" method="POST">
            <input type="text" name="name" required>
            <input type="email" name="email" required>
            <input type="tel" name="phone">
            <button type="submit">Submit Inquiry</button>
        </form>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_ecommerce():
    """Sample HTML content for e-commerce website."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ShopNow - Online Store</title>
        <meta name="description" content="Shop the latest products online">
    </head>
    <body>
        <nav>
            <a href="/">Home</a>
            <a href="/shop">Shop</a>
            <a href="/cart">Cart</a>
        </nav>
        <h1>Welcome to ShopNow</h1>
        <h2>Featured Products</h2>
        <div class="product">
            <h3>Product Name - $29.99</h3>
            <button class="add-to-cart">Add to Cart</button>
        </div>
        <a href="/checkout" class="cta">Checkout</a>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_saas():
    """Sample HTML content for SaaS website."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CloudApp - Project Management Software</title>
        <meta name="description" content="The best project management platform">
    </head>
    <body>
        <nav>
            <a href="/">Home</a>
            <a href="/features">Features</a>
            <a href="/pricing">Pricing</a>
            <a href="/demo">Request Demo</a>
        </nav>
        <h1>Manage Projects Like Never Before</h1>
        <h2>Features</h2>
        <ul>
            <li>Team collaboration</li>
            <li>Task automation</li>
            <li>API integrations</li>
        </ul>
        <a href="/signup" class="cta">Start Free Trial</a>
        <div class="pricing">
            <h3>Business Plan - $49/month</h3>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_headers_secure():
    """Sample secure HTTP headers."""
    return {
        "content-type": "text/html; charset=utf-8",
        "strict-transport-security": "max-age=31536000; includeSubDomains",
        "content-security-policy": "default-src 'self'",
        "x-frame-options": "DENY",
        "x-content-type-options": "nosniff",
        "referrer-policy": "strict-origin-when-cross-origin",
        "server": "nginx/1.18.0",
    }


@pytest.fixture
def sample_headers_insecure():
    """Sample insecure HTTP headers (missing security headers)."""
    return {
        "content-type": "text/html; charset=utf-8",
        "server": "Apache/2.4.41",
    }
