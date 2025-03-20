
if(document.querySelector('.hero___carousel') !== null){
    $('.hero___carousel').slick({
      margin:10,
      dots: true,
      infinite: true,
      // autoplay:true,
      autoPlayTimeout:2000,
      slidesToShow: 1,
      slidesToScroll: 1,
      arrows: false,
      responsive: [
          {
            breakpoint: 1024,
            settings: {
              slidesToShow: 1,
              slidesToScroll: 1,
              infinite: true,
              dots: true
            }
          },
          {
            breakpoint: 900,
            settings: {
              slidesToShow: 1,
              slidesToScroll: 1
            }
          },
          {
            breakpoint: 480,
            settings: {
              slidesToShow: 1,
              slidesToScroll: 1
            }
          }
        ]
    });
  }
  

  