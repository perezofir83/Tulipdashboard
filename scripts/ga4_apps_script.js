/**
 * Google Apps Script — GA4 Daily Report to Email
 *
 * Setup:
 * 1. Go to https://script.google.com → New Project
 * 2. Paste this entire script
 * 3. Replace GA4_PROPERTY_ID with your property ID (9-digit number from GA4 Admin → Property Settings)
 * 4. Replace EMAIL_TO with your email address
 * 5. Click Run → authorize when prompted
 * 6. Set up daily trigger: Triggers (clock icon) → Add Trigger → fetchGA4Daily → Time-driven → Day timer → 6am-7am
 *
 * The script pulls last 7 days of data by source/medium and emails a CSV.
 * The fetch_gmail_reports.py script will auto-detect it as GA4 data.
 */

// ============ CONFIGURATION ============
const GA4_PROPERTY_ID = '389376854';  // Tulip IL
const EMAIL_TO = 'perezofir83@gmail.com';  // ← Your email
const EMAIL_SUBJECT = 'GA4 Daily Report - Tulip Winery';
const DAYS_BACK = 7;
// =======================================

function fetchGA4Daily() {
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(today.getDate() - DAYS_BACK);

  const request = AnalyticsData.newRunReportRequest();

  // Date range
  const dateRange = AnalyticsData.newDateRange();
  dateRange.startDate = formatDate(startDate);
  dateRange.endDate = formatDate(today);
  request.dateRanges = [dateRange];

  // Dimensions
  request.dimensions = [
    newDimension('date'),
    newDimension('sessionSourceMedium'),
  ];

  // Metrics
  request.metrics = [
    newMetric('sessions'),
    newMetric('engagedSessions'),
    newMetric('engagementRate'),
    newMetric('averageSessionDuration'),
    newMetric('keyEvents'),
    newMetric('keyEventRate'),
    newMetric('eventsPerSession'),
    newMetric('totalRevenue'),
  ];

  // Order by date
  const orderBy = AnalyticsData.newOrderBy();
  orderBy.dimension = AnalyticsData.newDimensionOrderBy();
  orderBy.dimension.dimensionName = 'date';
  orderBy.dimension.orderType = 'ALPHANUMERIC';
  orderBy.desc = true;
  request.orderBys = [orderBy];

  // Limit to 10000 rows
  request.limit = 10000;

  // Run the report
  const report = AnalyticsData.Properties.runReport(request, 'properties/' + GA4_PROPERTY_ID);

  if (!report || !report.rows || report.rows.length === 0) {
    Logger.log('No data returned from GA4');
    return;
  }

  // Build CSV
  // Headers matching our expected schema
  const csvHeaders = [
    'Date',
    'Session source / medium',
    'Sessions',
    'Engaged sessions',
    'Engagement rate',
    'Average engagement time per session',
    'Key events',
    'Key event rate',
    'Events per session',
    'Total revenue',
  ];

  let csvContent = csvHeaders.join(',') + '\n';

  for (const row of report.rows) {
    const date = row.dimensionValues[0].value;  // YYYYMMDD format
    const formattedDate = date.substring(0, 4) + '-' + date.substring(4, 6) + '-' + date.substring(6, 8);

    const values = [
      formattedDate,
      '"' + (row.dimensionValues[1].value || '').replace(/"/g, '""') + '"',
      row.metricValues[0].value,
      row.metricValues[1].value,
      row.metricValues[2].value,
      row.metricValues[3].value,
      row.metricValues[4].value,
      row.metricValues[5].value,
      row.metricValues[6].value,
      row.metricValues[7].value,
    ];

    csvContent += values.join(',') + '\n';
  }

  // Send email with CSV attachment
  const blob = Utilities.newBlob(csvContent, 'text/csv', 'ga4_report.csv');

  GmailApp.sendEmail(EMAIL_TO, EMAIL_SUBJECT,
    'GA4 daily report for Tulip Winery\n' +
    'Period: ' + formatDate(startDate) + ' to ' + formatDate(today) + '\n' +
    'Rows: ' + report.rows.length,
    {
      attachments: [blob],
    }
  );

  Logger.log('Report sent! Rows: ' + report.rows.length);
}

// Helper: create dimension object
function newDimension(name) {
  const d = AnalyticsData.newDimension();
  d.name = name;
  return d;
}

// Helper: create metric object
function newMetric(name) {
  const m = AnalyticsData.newMetric();
  m.name = name;
  return m;
}

// Helper: format date as YYYY-MM-DD
function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return y + '-' + m + '-' + d;
}

// Manual test - run this to verify setup
function testRun() {
  Logger.log('Testing GA4 report fetch...');
  fetchGA4Daily();
  Logger.log('Done! Check your email.');
}
