const htmlblock = `
    <div class="container-fluid footer">
        <div class="col-xs-12 col-md-6 left">
            <a target="_blank" href="mailto:info@planscore.org"><img src="/images/email-logo.svg" /> info@planscore.org</a>
            &nbsp;
            <a target="_blank" href="https://twitter.com/PlanScore"><img src="/images/twitter-logo.svg" /> @PlanScore</a>
            &nbsp;
            <a target="_blank" href="https://github.com/PlanScore/PlanScore"><img src="/images/github-logo.svg" /> Github</a>
            <br>
            <span>PlanScore is a fiscally sponsored project of <a href="http://www.greeninfo.org/" target="_blank"><img src="/images/greeninfo.svg" /> GreenInfo Network</a></span>
        </div>
        <div class="col-xs-12 col-md-6 right">
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
