from szamlazz_collections_mcp import szamlazz_client


def test_generate_invoice_xml_contains_buyer():
    xml = szamlazz_client.build_xml(
        "generate_invoice.xml.j2",
        {
            "agent_key": "key",
            "buyer": {
                "name": "Teszt Kft.",
                "country": "HU",
                "zip": "1011",
                "city": "Budapest",
                "address": "Fo ut 1",
                "email": "teszt@example.com",
                "tax_number": None,
                "identifier": None,
            },
            "items": [],
            "payment_method": "átutalás",
            "currency": "HUF",
            "issue_date": "2024-01-01",
            "due_date": "2024-01-08",
            "invoice_language": "hu",
            "comment": None,
            "order_number": None,
            "external_id": None,
            "username": None,
            "password": None,
        },
    )
    assert "Teszt Kft." in xml
    assert "xmlszamla" in xml
