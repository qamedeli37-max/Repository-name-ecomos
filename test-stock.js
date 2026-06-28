const { default: YahooFinance } = require('yahoo-finance2');
const yf = new YahooFinance();

async function main() {
  const quote = await yf.quote('AAPL');
  console.log('price:', quote.regularMarketPrice);
  console.log('change%:', quote.regularMarketChangePercent);
  console.log('volume:', quote.regularMarketVolume);
  console.log('dayHigh:', quote.regularMarketDayHigh, 'dayLow:', quote.regularMarketDayLow);
  console.log('52wHigh:', quote.fiftyTwoWeekHigh, '52wLow:', quote.fiftyTwoWeekLow);
  console.log('prevClose:', quote.regularMarketPreviousClose);
  
  // Also get intraday data for 5-min candles
  const chart = await yf.chart('AAPL', {
    interval: '5m',
    range: '1d'
  });
  const candles = chart.quotes || [];
  console.log('Candles:', candles.length);
  if (candles.length > 0) {
    const last = candles[candles.length - 1];
    console.log('Last candle:', JSON.stringify(last));
  }
}
main().catch(e => console.error('Error:', e.message));
