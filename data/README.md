# Data Directory

Place the UCI Online Retail dataset here.

## Download

1. Visit https://archive.ics.uci.edu/dataset/352/online+retail
2. Click **Download** and extract the archive
3. Copy `Online Retail.xlsx` into this `data/` directory
4. The app will find it automatically when you click "Load from data/ folder" on the Settings page

## Alternative

You can also upload the file directly via the ⚙️ Settings page without placing it here.

## Expected filename

```
data/Online Retail.xlsx
```

## Compatible formats

- `Online Retail.xlsx` (recommended)
- Any CSV file exported from the same dataset with the same column names

## Required columns

| Column | Type | Description |
|--------|------|-------------|
| InvoiceNo | str | Invoice number (prefix 'C' = cancellation) |
| StockCode | str | Product code |
| Description | str | Product description |
| Quantity | int | Units purchased (negative for returns/cancellations) |
| InvoiceDate | datetime | Transaction timestamp |
| UnitPrice | float | Price per unit in GBP (£) |
| CustomerID | float | Customer identifier (NaN = unregistered) |
| Country | str | Customer country |
