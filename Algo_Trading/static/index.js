function deleteStock(stockId) {    
    fetch('/delete_stock', {
        method: "POST",
        body: JSON.stringify({ stockId: stockId })
    }).then((_res) => {
        window.location.reload()
    });
}

function getText(stock_name){
    fetch('/stock_page', {
        method: "POST",
        body: JSON.stringify({ stock_name: stock_name })
    }).then((_res) => {
        window.location.reload()
    });
    
}

window.setTimeout(function() {
    $(".alert").fadeTo(500, 0) 
}, 4000);
