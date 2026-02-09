Getting Started
==============

Installation
-----------

Tukuy can be installed using pip:

.. code-block:: bash

   pip install tukuy

Basic Usage
----------

Tukuy provides a flexible and powerful way to transform data with a simple, intuitive API. 
Here's a quick example to get you started:

.. code-block:: python

   from tukuy import TukuyTransformer

   # Create a transformer instance
   TUKUY = TukuyTransformer()

   # Basic text transformation
   text = " Hello World! "
   result = TUKUY.transform(text, [
       "strip",
       "lowercase",
       {"function": "truncate", "length": 5}
   ])
   print(result)  # "hello..."

Transformation Chains
--------------------

Tukuy allows you to chain multiple transformations together:

.. code-block:: python

   # Chain multiple transformations in a single call
   html = "<div>Hello <b>World</b>!</div>"
   result = TUKUY.transform(html, [
       "strip_html_tags",
       "lowercase"
   ])
   print(result)  # "hello world!"

   # Date transformation
   date_str = "2023-01-01"
   age = TUKUY.transform(date_str, [
       {"function": "age_calc"}
   ])
   print(age)  # Age in years

Validation
---------

Tukuy provides built-in validation for various data types:

.. code-block:: python

   # Email validation
   email = "test@example.com"
   valid = TUKUY.transform(email, ["email_validator"])
   print(valid)  # "test@example.com" or None if invalid

   # URL validation
   url = "https://example.com"
   valid = TUKUY.transform(url, ["url_validator"])
   print(valid)  # "https://example.com" or None if invalid

Next Steps
---------

* Explore the :doc:`user_guide` for more detailed instructions
* Check out the :doc:`examples` for practical use cases
* Browse the :doc:`modules` for API reference