function showtime(){
    let d = new Date();
    document.getElementById("date").innerHTML = d;
    setTimeout(showtime, 1000);
}