(function() {
    function cleanCellText(cell) {
        return (cell.innerText || cell.textContent || '').replace(/\s+/g, ' ').trim();
    }

    function csvEscape(value) {
        const text = String(value == null ? '' : value);
        if (/[",\n]/.test(text)) {
            return `"${text.replace(/"/g, '""')}"`;
        }
        return text;
    }

    function timestamp() {
        const now = new Date();
        const pad = value => String(value).padStart(2, '0');
        return [
            now.getFullYear(),
            pad(now.getMonth() + 1),
            pad(now.getDate())
        ].join('') + '-' + [
            pad(now.getHours()),
            pad(now.getMinutes()),
            pad(now.getSeconds())
        ].join('');
    }

    function shouldSkipColumn(header) {
        const label = cleanCellText(header).toLowerCase();
        return header.querySelector('input[type="checkbox"]') || label === 'actions' || label === 'action';
    }

    window.downloadSelectedRowsBeforeDelete = function(checkboxSelector, baseFilename) {
        const selectedCheckboxes = Array.from(document.querySelectorAll(checkboxSelector));
        if (!selectedCheckboxes.length) {
            alert('Please select at least one record to delete');
            return false;
        }

        const table = selectedCheckboxes[0].closest('table');
        if (!table) {
            alert('Unable to prepare the download for the selected records.');
            return false;
        }

        const headerCells = Array.from(table.querySelectorAll('thead tr:last-child th'));
        const includedColumnIndexes = headerCells
            .map((header, index) => ({ header, index }))
            .filter(item => !shouldSkipColumn(item.header))
            .map(item => item.index);

        const headers = includedColumnIndexes.map(index => cleanCellText(headerCells[index]) || `Column ${index + 1}`);
        const rows = selectedCheckboxes.map(checkbox => {
            const row = checkbox.closest('tr');
            const cells = row ? Array.from(row.children) : [];
            return includedColumnIndexes.map(index => cleanCellText(cells[index]));
        });

        const csv = [headers, ...rows]
            .map(row => row.map(csvEscape).join(','))
            .join('\n');

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const filename = `${baseFilename || 'records-before-delete'}-${timestamp()}.csv`;
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
        return true;
    };
})();
