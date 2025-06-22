import json
import csv
import os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from datetime import datetime


model_path = "./models/local_smol_model/"

tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True)

# Load Local SmolLM2 model
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Load SmolLM2-360M model
# pipe = pipeline("text-generation", model="HuggingFaceTB/SmolLM2-360M")


def build_prompt(invoice_text: str) -> str:
    return f"""
    You are an expert invoice data extractor. Extract the following fields from the invoice text:
    'invoice_number', 'invoice_date' (formatYYYY-MM-DD), 'due_date' (formatYYYY-MM-DD),
    'vendor_name', 'vendor_address', 'gstin', 'total_amount', 'tax_amount', 'currency', 'purchase_order_number',
    'line_items' (as a list of objects, each with 'description', 'quantity', 'unit_price', 'line_total').
    If a field is not found, use null. For amounts, extract only the numerical value without currency symbols or commas.
    For dates, use YYYY-MM-DD format.

    Invoice Text:
    ---
    {invoice_text}
    ---

    Provide the output strictly as only a JSON object. Example JSON structure:
    {{
      "invoice_number": "INV-123",
      "invoice_date": "2024-01-15",
      "due_date": "2024-02-15",
      "vendor_name": "ABC Corp",
      "vendor_address": "123 Main St, City, Country",
      "gstin": "GSTIN123456789",
      "total_amount": 1000.50,
      "tax_amount": 180.00,
      "currency": "INR",
      "purchase_order_number": "PO-987",
      "line_items": [
        {{
          "description": "Product A",
          "quantity": 2,
          "unit_price": 250.00,
          "line_total": 500.00
        }},
        {{
          "description": "Service B",
          "quantity": 1,
          "unit_price": 500.50,
          "line_total": 500.50
        }}
      ]
    }}
    """


def extract_entities(invoice_text: str) -> dict:
    prompt = build_prompt(invoice_text)
    output = pipe(prompt, max_new_tokens=512, do_sample=False)[0]['generated_text']

    # The model might echo the prompt; strip it
    print("Model output:", output)
    generated_json_str = output.replace(prompt, "").strip()
    try:
        json_obj = json.loads(generated_json_str)
        return json_obj
    except json.JSONDecodeError:
        raise ValueError("Model output is not valid JSON.")