
///////////////////////////////////////////////////////// Box light slide(1) //////////////////////////////////////////////////////////////
function openModal() {
    document.getElementById("lightbox").style.display = "flex";
}

function closeModal() {
    document.getElementById("lightbox").style.display = "none";
}

//
var slideIndex = 1;
showSlides(slideIndex);

function plusSlides(n) {
    showSlides(slideIndex += n);
}

function currentSlide(n) {
    showSlides(slideIndex = n);
}

function showSlides(n) {
    var i;
    var slides = document.getElementsByClassName("mySlides");
    if (n > slides.length) { slideIndex = 1 }
    if (n < 1) { slideIndex = slides.length }
    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }

    slides[slideIndex - 1].style.display = "flex";
}

/////////////////////////////////////////////////////////  Defualte slide(2) //////////////////////////////////////////////////////////////

var slideIndex2 = 1;
showSlides2(slideIndex2);

function plusSlides2(n) {
    showSlides2(slideIndex2 += n);
}

function currentSlide2(n) {
    showSlides2(slideIndex2 = n);
}

function showSlides2(n) {
    var i;
    var slides = document.getElementsByClassName("mySlides2");
    if (n > slides.length) { slideIndex2 = 1 }
    if (n < 1) { slideIndex2 = slides.length }
    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }

    slides[slideIndex2 - 1].style.display = "flex";
}

/////////////////////////////////////////////////////////  Side Bar menu //////////////////////////////////////////////////////////////

ulSpan = document.getElementById('ulspan');

function showSideBar() {

    ulSpan.setAttribute('class', "sidebar");
    document.querySelector('#ulspan img').style.display = "block";
}

function closeSlideBar() {
    ulSpan.removeAttribute('class', "sidebar");
    document.querySelector('#ulspan img').style.display = "none";
}

///////////////////////////////////////////////////////// add to cart orders //////////////////////////////////////////////////////////////

function showCart() {
    if (document.querySelector('.cart').style.display == "none"){
        document.querySelector('.cart').style.display = "block";
        generatCartItems();
    }
    else
        document.querySelector('.cart').style.display = "none";
}
var total = 1;
var Result = null;

function plus() {
    ManageChanges();
    if (Result == null){
        Result = document.getElementById('quantityHolder');
    }
    const deductSpan = document.getElementById("deducted");
    const priceSpan = document.getElementById("amount");
    const price = priceSpan.dataset.price;
    total += 1;
    const resulted_price = (price*total).toFixed(2);
    Result.textContent = total;
    priceSpan.textContent = resulted_price;
    if (total > 1 && deductSpan)
        deductSpan.textContent = `-$${deductSpan.dataset.amount*total}`;
}

function minus() {
    ManageChanges();
    if (Result == null){
        Result = document.getElementById('quantityHolder');
    }
    const priceSpan = document.getElementById("amount");
    const deductSpan = document.getElementById("deducted");
    if (Result.innerHTML > 1) {
        const price = priceSpan.dataset.price;
        total -= 1;
        const resulted_price = (price*total).toFixed(2);
        Result.textContent = total;
        priceSpan.textContent = resulted_price;
        if (deductSpan){
            deductSpan.textContent = `-$${deductSpan.dataset.amount*total}`;
        }
    }
}

///////////////////////////////////////////////////////// Cart  //////////////////////////////////////////////////////////////

function ob(item, price, count) {
    this.item = item;
    this.price = price;
    this.count = count;
}

var cart = [];

num =  document.getElementById('num');
num.innerHTML = cart.length;

function addItem() {
    var newItem = new ob();
    newItem.name = document.getElementById('name').innerHTML;
    newItem.price = document.getElementById('amount').innerHTML;
    newItem.count = Result.innerHTML;
    cart.push(newItem);
    num.innerHTML = cart.length;
    generatCartItems();
}

function dropItem(i){
    //delete cart[i];
    cart.pop(i);
    generatCartItems();
}
const cartContainer = document.querySelector('.cart');

function generatCartItems(){
    if(cart.length == 0){
        var empty = '<h3>Cart</h3><p id ="empty">Your cart is empty.</p>';
        cartContainer.innerHTML = empty;
        //cartContainer.insertAdjacentHTML('beforeend',empty)      
    }

    else{
        cartContainer.innerHTML = '<h3>Cart</h3>';
        for(i=0;i<cart.length;i++){
            cartContainer.insertAdjacentHTML('beforeend',
            `<div class="item">
            <img src="images/image-product-1-thumbnail.jpg" alt="" style="height: 60px;">
            <p>${cart[i].name} $${cart[i].price} x ${cart[i].count} <strong>$${cart[i].price * cart[i].count}</strong></p>
            <img src="images/icon-delete.svg" alt="" onclick="dropItem(${i})" class="cursor">
          </div>`
            ) ;
        }
        cartContainer.insertAdjacentHTML('beforeend','<button>Checkout</button>');
    }
}