export function writeSize(value)
{
    if (value < 1000)
        return Math.round(value) + "b";
    if (value < 1000 * 1000)
        return Math.round(value / 1000) + "kb";
    if (value < 1000 * 1000 * 1000)
        return Math.round(value / (1000 * 1000) * 100) / 100 + "mb";
    if (value < 1000 * 1000 * 1000 * 1000)
        return Math.round(value / (1000 * 1000 * 1000) * 100) / 100 + "gb";
    return Math.round(value / (1000 * 1000 * 1000 * 1000) * 100) / 100 + "tb";
}

export function writeSpeed(value)
{
    return writeSize(value) + "ps";
}

export function writeTimespan(duration)
{
     duration = Math.round(duration);
     var seconds = parseInt((duration / 1000) % 60),
     minutes = parseInt((duration / (1000 * 60)) % 60),
     hours = parseInt((duration / (1000 * 60 * 60)) % 24);

     hours = (hours < 10) ? "0" + hours : hours;
     minutes = (minutes < 10) ? "0" + minutes : minutes;
     seconds = (seconds < 10) ? "0" + seconds : seconds;

     if (hours > 0)
        return hours + ":" + minutes + ":" + seconds;
     return minutes + ":" + seconds;
}

export function writeNumber(value)
{
    if (isNaN(value))
        return 0;

    var f = Math.round(parseFloat(value));
    if(f > 1000)
        f = (Math.round(f / 100) / 10) + "k";
    return f;
}

export function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

export function formatTime(milliseconds_value, year, month, day, hour, minute, second){
    return new Intl.DateTimeFormat('en-GB', {
    year: year ? 'numeric': undefined,
    month: month? 'short': undefined,
    day: day? '2-digit': undefined,
    hour: hour? '2-digit': undefined,
    minute: minute? '2-digit': undefined,
    second: second? '2-digit': undefined, }).format(milliseconds_value)
}

export function formatTemperature(value){
     return (Math.round(value / 10) / 10) + "°C";
}