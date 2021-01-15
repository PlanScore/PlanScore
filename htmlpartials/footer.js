const htmlblock = `
    <div class="container-fluid footer">
    <div class="row">
        <p class="col-md-2">
            <a target="_blank" href="mailto:info@planscore.org"><img src="https://planscore.org/images/email-logo.svg"> info@planscore.org</a>
        </p>
        <p class="col-md-2">
            <a target="_blank" href="https://twitter.com/PlanScore"><img src="https://planscore.org/images/twitter-logo.svg"> @PlanScore</a>
        </p>
        <p class="col-md-2">
            <a target="_blank" href="https://github.com/PlanScore/PlanScore"><img src="https://planscore.org/images/github-logo.svg"> Github</a>
        </p>
        <form class="col-md-2" action="https://www.paypal.com/donate" method="post" target="_top">
            <input type="hidden" name="hosted_button_id" value="C9G45F294EKEG" />
            <input type="image" src="https://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif" border="0" name="submit" title="PayPal - The safer, easier way to pay online!" alt="Donate with PayPal button" />
            <img alt="" border="0" src="https://www.paypal.com/en_US/i/scr/pixel.gif" width="1" height="1" />
        </form>
    </div>
    <div class="row">
        <span class="col-md-12">
            PlanScore is a 501(c)(3) non-profit organization, EIN 83-1367310
        </span>
    </div>
    </div>

    <script async src="https://www.googletagmanager.com/gtag/js?id=UA-65629552-4"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', 'UA-65629552-4');
    </script>
    `;
module.exports = htmlblock;
