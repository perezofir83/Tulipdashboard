/**
 * Google Apps Script — Google Ads Daily Report to Email
 *
 * Setup:
 * 1. Go to https://ads.google.com/aw/bulkactions/scripts (in your Tulip account)
 *    OR: Tools → Scripts
 * 2. Click "+ New Script"
 * 3. Paste this entire script
 * 4. Replace EMAIL_TO with your email
 * 5. Click "Preview" to test → check your email
 * 6. Click "Run frequency" → Daily at 8:00 AM
 *
 * This runs INSIDE Google Ads (not Google Apps Script editor).
 * It pulls yesterday's campaign data and emails a CSV.
 */

// ============ CONFIGURATION ============
var EMAIL_TO = 'perezofir@gmail.com';
var EMAIL_SUBJECT = 'Google Ads Daily Report - Tulip Winery';
// =======================================

function main() {
  // Get yesterday's date
  var yesterday = getDateString(-1);
  var today = getDateString(0);

  // Pull last 7 days, only ENABLED campaigns
  var weekAgo = getDateString(-7);

  var query =
    "SELECT " +
      "segments.date, " +
      "campaign.name, " +
      "campaign.status, " +
      "campaign.advertising_channel_type, " +
      "ad_group.name, " +
      "metrics.impressions, " +
      "metrics.clicks, " +
      "metrics.cost_micros, " +
      "metrics.conversions, " +
      "metrics.conversions_value, " +
      "metrics.ctr, " +
      "metrics.average_cpc, " +
      "metrics.interactions " +
    "FROM ad_group " +
    "WHERE segments.date BETWEEN '" + weekAgo + "' AND '" + yesterday + "' " +
      "AND campaign.status = 'ENABLED' " +
    "ORDER BY segments.date DESC, campaign.name, ad_group.name";

  var report = AdsApp.search(query);

  // Build CSV
  var csvHeaders = [
    'Date',
    'Campaign',
    'Campaign status',
    'Campaign type',
    'Ad group',
    'Impressions',
    'Clicks',
    'Cost',
    'Conversions',
    'Conv. value',
    'CTR',
    'Avg. CPC',
    'Interactions'
  ];

  var csvContent = csvHeaders.join(',') + '\n';
  var rowCount = 0;

  while (report.hasNext()) {
    var row = report.next();

    var date = row.segments.date;
    var campaignName = row.campaign.name;
    var campaignStatus = row.campaign.status;
    var channelType = row.campaign.advertisingChannelType;
    var adGroupName = row.adGroup.name;
    var impressions = row.metrics.impressions;
    var clicks = row.metrics.clicks;
    var costMicros = row.metrics.costMicros || 0;
    var cost = (costMicros / 1000000).toFixed(2);
    var conversions = row.metrics.conversions || 0;
    var convValue = row.metrics.conversionsValue || 0;
    var ctr = row.metrics.ctr || 0;
    var avgCpc = row.metrics.averageCpc || 0;
    var avgCpcIls = (avgCpc / 1000000).toFixed(2);
    var interactions = row.metrics.interactions || 0;

    var values = [
      date,
      '"' + campaignName.replace(/"/g, '""') + '"',
      campaignStatus,
      channelType,
      '"' + adGroupName.replace(/"/g, '""') + '"',
      impressions,
      clicks,
      cost,
      conversions,
      convValue,
      (ctr * 100).toFixed(2) + '%',
      avgCpcIls,
      interactions
    ];

    csvContent += values.join(',') + '\n';
    rowCount++;
  }

  if (rowCount === 0) {
    Logger.log('No data for ' + yesterday);
    return;
  }

  // Send email — CSV in body (between markers) + as attachment
  MailApp.sendEmail({
    to: EMAIL_TO,
    subject: EMAIL_SUBJECT,
    body: 'Google Ads daily report for Tulip Winery\n' +
          'Period: ' + weekAgo + ' to ' + yesterday + '\n' +
          'Rows: ' + rowCount + ' (active campaigns only)\n\n' +
          '---CSV_START---\n' + csvContent + '---CSV_END---',
    attachments: [
      Utilities.newBlob(csvContent, 'text/csv', 'google_ads_report.csv')
    ]
  });

  Logger.log('Report sent! Period: ' + weekAgo + ' to ' + yesterday + ', Rows: ' + rowCount);
}

function getDateString(daysOffset) {
  var date = new Date();
  date.setDate(date.getDate() + daysOffset);
  var y = date.getFullYear();
  var m = ('0' + (date.getMonth() + 1)).slice(-2);
  var d = ('0' + date.getDate()).slice(-2);
  return y + '-' + m + '-' + d;
}
