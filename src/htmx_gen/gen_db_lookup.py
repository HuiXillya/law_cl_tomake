
from src.string_management import TasksKey, AnnKey


def gen_looked(ann_list):
    tr_list = []
    ann_list_sorted = sorted(ann_list, key=lambda x: x.get(AnnKey.DATE.value), reverse=True)
    for ann in ann_list_sorted:
        tr = f"""
        <tr>
            <td>{ann.get(AnnKey.DATE.value)}</td>
            <td><a href="{ann.get(AnnKey.LINK.value)}">連結</a></td>
            <td>{ann.get(AnnKey.TITLE.value)}</td>
            <td>{ann.get(AnnKey.DEPARTMENTS.value)}</td>
        </tr>
        """
        tr_list.append(tr)
    looed_wrapper = f"""
    <table id="db_looked_table" class="lookup_table">
        <caption>
            <thead>
                <tr>
                    <th>日期</th>
                    <th>連結</th>
                    <th>主旨</th>
                    <th>相關部門</th></tr></thead>
            <tbody>
            {"".join(tr_list)}
            </tbody>
        </caption>
    </table>
    """
    return looed_wrapper
