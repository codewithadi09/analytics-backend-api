/**
 * start_date/end_date as YYYY-MM-DD strings (date input value format).
 * Every analytics domain except the Journey detail view accepts these
 * as optional inclusive-range query params — see traffic.py, conversion.py,
 * navigation.py, engagement.py, interactions.py, form_dropoff.py, and
 * dropoff_explorer.py, all confirmed to expose start_date/end_date.
 */
export type DateRangeParams = {
  start_date?: string;
  end_date?: string;
};
