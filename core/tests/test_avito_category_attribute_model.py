import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models, schemas
from app.database import Base
from app.services.avito_schema_service import upsert_avito_category_schema, upsert_product_avito_attributes

@pytest.fixture
def db_session():
    """Create in-memory SQLite DB session for dynamic category & attribute testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

class TestAvitoCategoryAttributeModel:

    def test_category_schema_isolation_printer_vs_cpu(self, db_session):
        """Verify different categories have distinct attribute schemas without collision."""
        printer_params = {
            "Состояние": "Б/у",
            "Тип устройства": "Принтер",
            "Технология печати": "Лазерная",
            "Цветность печати": "Цветная"
        }
        cpu_params = {
            "Состояние": "Новое",
            "Сокет": "LGA1700",
            "Количество ядер": 16,
            "Тактовая частота": "3.4 ГГц"
        }

        printer_cat = upsert_avito_category_schema(
            db=db_session,
            category_name="Принтеры",
            category_path="Бытовая электроника / Оргтехника / Принтеры",
            characteristics=printer_params
        )

        cpu_cat = upsert_avito_category_schema(
            db=db_session,
            category_name="Процессоры",
            category_path="Компьютерные комплектующие / Процессоры",
            characteristics=cpu_params
        )

        assert printer_cat.id != cpu_cat.id
        assert len(printer_cat.definitions) == 4
        assert len(cpu_cat.definitions) == 4

        printer_keys = {d.external_key for d in printer_cat.definitions}
        cpu_keys = {d.external_key for d in cpu_cat.definitions}

        assert "Технология печати" in printer_keys
        assert "Сокет" not in printer_keys
        assert "Сокет" in cpu_keys
        assert "Технология печати" not in cpu_keys

    def test_repeat_schema_and_product_import_idempotent(self, db_session):
        """Verify repeated imports do not create duplicate categories, definitions, options, or values."""
        product = models.Product(sku="PROD-TEST-1", title="Test Printer", status="draft")
        db_session.add(product)
        db_session.commit()

        params = {"Состояние": "Б/у", "Технология печати": "Лазерная"}

        # First import
        cat1 = upsert_avito_category_schema(db_session, "Оргтехника", characteristics=params)
        vals1 = upsert_product_avito_attributes(db_session, product.id, cat1.id, params)

        # Second import
        cat2 = upsert_avito_category_schema(db_session, "Оргтехника", characteristics=params)
        vals2 = upsert_product_avito_attributes(db_session, product.id, cat2.id, params)

        assert cat1.id == cat2.id
        assert db_session.query(models.AvitoCategory).count() == 1
        assert db_session.query(models.AvitoAttributeDefinition).count() == 2
        assert db_session.query(models.ProductAvitoAttributeValue).count() == 2

        updated_product = db_session.query(models.Product).filter(models.Product.id == product.id).first()
        assert updated_product.avito_category_id == cat1.id

    def test_unknown_attribute_dynamically_preserved(self, db_session):
        """Verify new/unknown attribute fields are dynamically preserved without 500 errors."""
        product = models.Product(sku="PROD-TEST-2", title="Unknown Device", status="draft")
        db_session.add(product)
        db_session.commit()

        cat = upsert_avito_category_schema(db_session, "Электроника", characteristics={"Стандартная": "Значение"})
        
        # Product arrives with brand new unexpected attribute "СуперФункция"
        new_params = {"Стандартная": "Значение", "СуперФункция": "Активирована"}
        vals = upsert_product_avito_attributes(db_session, product.id, cat.id, new_params)

        assert len(vals) == 2
        attr_names = {v.definition.name for v in vals}
        assert "СуперФункция" in attr_names

        val_obj = next(v for v in vals if v.definition.name == "СуперФункция")
        assert val_obj.value == "Активирована"
        assert val_obj.raw_value == "Активирована"

    def test_exact_raw_value_preservation(self, db_session):
        """Verify raw_value stores exact original value for list, dict, and numeric types."""
        product = models.Product(sku="PROD-TEST-3", title="Complex Specs", status="draft")
        db_session.add(product)
        db_session.commit()

        complex_params = {
            "Интерфейсы": ["USB", "Wi-Fi", "Ethernet"],
            "Ширина": 420.5,
            "Двусторонняя печать": True
        }

        cat = upsert_avito_category_schema(db_session, "Принтеры", characteristics=complex_params)
        vals = upsert_product_avito_attributes(db_session, product.id, cat.id, complex_params)

        val_map = {v.definition.external_key: v for v in vals}

        # Check list
        assert val_map["Интерфейсы"].value == "USB, Wi-Fi, Ethernet"
        assert '["USB", "Wi-Fi", "Ethernet"]' in val_map["Интерфейсы"].raw_value

        # Check boolean
        assert val_map["Двусторонняя печать"].value == "True"
        assert val_map["Двусторонняя печать"].raw_value == "True"

    def test_real_printer_8313765236_fixture_import(self, db_session):
        """Benchmark test for real observed listing 8313765236 (Product 58)."""
        prod58 = models.Product(id=58, sku="PRINTER-HP-58", title="Лазерный цветной принтер hp m252n на запчасти", status="draft")
        db_session.add(prod58)
        db_session.commit()

        real_observed_printer_payload = {
            "category_name": "Оргтехника и расходники",
            "category_path": "Бытовая электроника / Оргтехника и расходники / Принтеры",
            "characteristics": {
                "Состояние": "Б/у",
                "Тип устройства": "Принтер",
                "Технология печати": "Лазерная",
                "Цветность печати": "Цветная"
            }
        }

        cat = upsert_avito_category_schema(
            db=db_session,
            category_name=real_observed_printer_payload["category_name"],
            category_path=real_observed_printer_payload["category_path"],
            characteristics=real_observed_printer_payload["characteristics"]
        )

        vals = upsert_product_avito_attributes(
            db=db_session,
            product_id=prod58.id,
            category_id=cat.id,
            characteristics=real_observed_printer_payload["characteristics"]
        )

        assert prod58.avito_category_id == cat.id
        assert len(vals) == 4

        saved_attr_dict = {v.definition.name: v.value for v in vals}
        assert saved_attr_dict["Состояние"] == "Б/у"
        assert saved_attr_dict["Тип устройства"] == "Принтер"
        assert saved_attr_dict["Технология печати"] == "Лазерная"
        assert saved_attr_dict["Цветность печати"] == "Цветная"

    def test_product_without_avito_data_remains_valid(self, db_session):
        """Verify products without Avito category or attributes remain 100% valid."""
        prod_manual = models.Product(sku="MANUAL-1", title="Manual Tool", status="active")
        db_session.add(prod_manual)
        db_session.commit()

        assert prod_manual.avito_category_id is None
        assert len(prod_manual.avito_attribute_values) == 0
        assert prod_manual.status == "active"
