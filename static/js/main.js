// カードクリック → モーダル表示
  $(document).on("click", ".goods-list .card", function () {
    const itemId = $(this).data("item-id");
    if (!itemId) return;

    $("#modalOverlay").load(`/items/${itemId}/modal`, function () {
      requestAnimationFrame(() => {
        $("#modalOverlay").addClass("is-open");
      });
    });
  });

  // モーダル閉じる
  $(document).on("click", "#modalOverlay, #closeModal", function (e) {
    if (e.target.id !== "modalOverlay" && e.target.id !== "closeModal") return;
  
    if (window.innerWidth <= 430) {
      $(".modal").css("transform", "translateY(100%)");
      setTimeout(() => {
        $("#modalOverlay").removeClass("is-open").empty();
      }, 350);
    } else {
      $("#modalOverlay").removeClass("is-open").empty();
    }
  });

  function showLoading() {
    document.getElementById("loading").style.display = "flex";
}

function hideLoading() {
    document.getElementById("loading").style.display = "none";
}



