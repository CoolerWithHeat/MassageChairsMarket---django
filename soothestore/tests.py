product_meta_data = {
    "meta_description": "The sleekly designed Certus by Human Touch® is not only eye-catching but also remarkably functional. Ideal for your wellness routine.",
    "meta_keywords": "massage chair, Certus, Human Touch, wellness, health, self-care",
    "og_title": "Certus Massage Chair by Human Touch - Reliable Wellness Companion",
    "og_description": "Experience the sleek design and top functionality of the Certus Massage Chair by Human Touch. A reliable companion on your wellness journey.",
    "og_image": "https://www.example.com/images/certus-massage-chair.jpg",  # Replace with the actual image URL
    "og_url": "https://www.massagechairsmarket.com/products/certus-massage-chair",
    "og_type": "product",
}

import requests
request = requests.post('http://192.168.5.22:8000/serverdestination/Product_Meta/92/', json=product_meta_data)
print(request.json())

# meta_description, meta_keywords, og_title, og_image, og_url, og_type