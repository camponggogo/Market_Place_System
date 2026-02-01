"""
หมายเลข token ประจำร้านค้า 20 หลัก
token = group_id(3) + site_id(4) + store_id(6) + menu_id(7)
"""


def generate_store_token(
    group_id: int,
    site_id: int,
    store_id: int,
    menu_id: int = 0,
) -> str:
    """
    สร้าง token 20 หลักประจำร้านค้า
    - group_id: 3 หลัก (zero-pad)
    - site_id: 4 หลัก (zero-pad)
    - store_id: 6 หลัก (zero-pad)
    - menu_id: 7 หลัก (zero-pad, 0 = ระดับร้าน)
    """
    return (
        str(group_id).zfill(3)
        + str(site_id).zfill(4)
        + str(store_id).zfill(6)
        + str(menu_id).zfill(7)
    )
