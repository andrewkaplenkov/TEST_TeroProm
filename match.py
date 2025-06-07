from logging import Logger
from typing import Optional
import click
import pandas as pd
from pathlib import Path
from rapidfuzz import process, fuzz
import re



CURRENT_DIR = Path(__file__).resolve().parent
DATA_FOLDER = "data"
CATEGORIES_PATH = CURRENT_DIR / DATA_FOLDER / "Дерево категорий.xlsx"
SUPPLIER_PATH = CURRENT_DIR / DATA_FOLDER / "Данные поставщика.xlsx"

def match(product_id: int = 88785, score_threshold: int = 80) -> Optional[int]:

    try:
        category_df = pd.read_excel(CATEGORIES_PATH)
        supplier_df = pd.read_excel(SUPPLIER_PATH)
    except Exception as e:
        print(f"Ошибка при загрузке файлов: {e}")
        return None


    supplier_df = supplier_df.rename(columns={
        "Код артикула": "product_id",
        "Название": "name",
        "Раздел": "group",
    }).dropna(subset=["product_id", "name"])[["product_id", "name", "group"]]

    row = supplier_df[supplier_df["product_id"] == product_id]
    if row.empty:
        print(f"Товар с идентификатором {product_id} не найден в файле поставщика")
        return None

    product_name, product_group = [
        row.iloc[0]["name"],
        row.iloc[0]["group"],
    ]

    search_str = f"{clean_text(product_group)}/{clean_text(product_name)}"

    print(f"Товар с идентификатором '{product_id}' имеет название '{product_name}'")

    products_group_name_list = category_df[["cat_1", "cat_3"]].astype(str).agg("/".join, axis=1).tolist()

    match_result = process.extractOne(
        query=search_str,
        choices=products_group_name_list,
        scorer=fuzz.token_set_ratio,
    )

    if match_result is None:
        print(f"Ошибка.")
        return None

    best_match, score, match_idx = match_result

    category_id, category_name = category_df.iloc[match_idx][["cat_id", "cat_0"]].astype(str).tolist()

    if score >= score_threshold:
        print(
            f"""
            Для товара с идентификатором '{product_id}'
            определена категория с идентификатором '{category_id}'
            название категории '{category_name}'
            """
        )
    else:
        print(
            f"""
            Для товара с идентификатором '{product_id}'
            не найдено совпадений выше порога {score_threshold}%
            Лучшее совпадение ({round(score, 2)}%):
            идентификатор категории: {category_id}
            название категории: {category_name}
            """
        )

def clean_text(text: str) -> str:
    text = re.sub(r'\b[хx]\s*\d+[.,]?\d*\s*(мм|см|мл|г|кг|л)?\b', '', text)
    text = re.sub(r'\b\d+[.,]?\d*\b', '', text)
    text = re.sub(r'\b(мм|см|мл|г|кг|л|тип|шт)\b', '', text)
    text = re.sub(r'[^А-Яа-яё0-9/\s]', '', text)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


@click.command(help="Определяет категорию товара по его идентификатору")
@click.option("--product-id", required=True, type=int, help="Идентификатор искомого товара")
@click.option("--score-threshold", type=int, default=80, help="Минимальный порог схожести для сопоставления (по умолчанию 80%)")
def main(product_id: int, score_threshold) -> None:
    match(product_id, score_threshold)

if __name__ == "__main__":
    main()



