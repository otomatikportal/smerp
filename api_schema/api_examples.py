#Flush the db and execute in order for test!

MATERIAL_BULK_CREATE_EXAMPLE = [
  {
    "name": "Tedarik Malzemesi 1",
    "category": "supplied",
    "description": "Tedarik edilen malzeme açıklaması"
  },
  {
    "name": "Karton Koli",
    "category": "cardboard",
    "description": "Koli ve karton ürün açıklaması"
  },
  {
    "name": "Parça Yarı Mamul",
    "category": "part",
    "description": "Parça veya yarı mamul açıklaması"
  },
  {
    "name": "Satılabilir Ürün",
    "category": "good",
    "description": "Satışa uygun ürün açıklaması"
  },
  {
    "name": "İdari Malzeme",
    "category": "administrative",
    "description": "İdari işler için malzeme açıklaması"
  },
    {
    "name": "Tedarik Malzemesi 2",
    "category": "supplied",
    "description": "İkinci tedarik edilen malzeme"
  },
  {
    "name": "Karton Kutu",
    "category": "cardboard",
    "description": "Küçük boy karton kutu"
  },
  {
    "name": "Yarı Mamul Parça",
    "category": "part",
    "description": "Üretimde kullanılan yarı mamul"
  },
  {
    "name": "Satış Ürünü A",
    "category": "good",
    "description": "Satışa sunulan ürün A"
  },
  {
    "name": "Ofis Sandalyesi",
    "category": "administrative",
    "description": "İdari işler için sandalye"
  },
  {
    "name": "Ahşap Palet",
    "category": "pallet",
    "description": "Depolama için ahşap palet"
  },
  {
    "name": "Belirtilmemiş Malzeme",
    "category": "undefined",
    "description": "Kategoriye atanmamış malzeme"
  },
  {
    "name": "Tedarik Malzemesi 3",
    "category": "supplied",
    "description": "Üçüncü tedarik edilen malzeme"
  },
  {
    "name": "Büyük Karton Koli",
    "category": "cardboard",
    "description": "Büyük boy koli"
  },
  {
    "name": "Parça C",
    "category": "part",
    "description": "C tipi parça"
  }
]

COMPANY_CREATE_EXAMPLE = {
    "name": "Örnek Şirket",
    "legal_name": "Ornek Ticaret Limited Şirketi",
    "e_mail": "info@ornek.com",
    "website": "https://www.ornek.com",
    "phone": "02121234567",
    "description": "Test için örnek şirket açıklaması.",
    "contacts": [
        {
            "name": "Ahmet",
            "last_name": "Yılmaz",
            "gender": "e",
            "role": "owner",
            "e_mail": "ahmet.yilmaz@ornek.com",
            "phone": "05551234567",
            "description": "Şirket sahibi."
        },
        {
            "name": "Ayşe",
            "last_name": "Kara",
            "gender": "k",
            "role": "employee",
            "e_mail": "ayse.kara@ornek.com",
            "phone": "05557654321",
            "description": "Satış departmanı çalışanı."
        }
    ]
}

PROCUREMENT_ORDER_CREATE_EXAMPLE = {
  "payment_term": "NET_T",
  "payment_method": "BANK_TRANSFER",
  "incoterms": "FOB",
  "trade_discount": 0.05,
  "due_in_days": "30 00:00:00",
  "due_discount": 0.01,
  "due_discount_days": "10 00:00:00",
  "description": "Toplu tedarik siparişi",
  "currency": "TRY",
  "delivery_address": "Merkez depo, İstanbul",
  "vendor": 1,
  "lines": [
    {
      "material": 1,
      "uom": "ADT",
      "quantity": 100,
      "unit_price": 25.5,
      "tax_rate": 0.18
    },
    {
      "material": 2,
      "uom": "BOX",
      "quantity": 50,
      "unit_price": 12.0,
      "tax_rate": 0.08
    },
    {
      "material": 3,
      "uom": "ADT",
      "quantity": 200,
      "unit_price": 7.75,
      "tax_rate": 0.18
    },
    {
      "material": 4,
      "uom": "ADT",
      "quantity": 30,
      "unit_price": 120.0,
      "tax_rate": 0.18
    },
    {
      "material": 5,
      "uom": "ADT",
      "quantity": 10,
      "unit_price": 350.0,
      "tax_rate": 0.18
    }
  ]
}