const htmlblock = `
    <nav class="navbar navbar-default">
        <div class="container">
            <div class="navbar-header">
                <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false">
                    <span class="sr-only">Toggle navigation</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </button>
                <a class="navbar-brand" href="../home/"><img id="brand-logo" src="../images/logo.svg"></img></a>
            </div>
            <div class="collapse navbar-collapse" id="navbar">
                <ul class="nav navbar-nav navbar-right">
                    <li><a href="../scoreyours/">Score a Plan</a></li>
                    <li><a href="../about/">What is PlanScore?</a></li>
                </ul>
            </div>
        </div>
    </nav>
`;
module.exports = htmlblock;
